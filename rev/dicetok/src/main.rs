use ansi_to_tui::IntoText;
use arc_swap::ArcSwap;
use crossterm::event::{self, Event, KeyCode, KeyEvent, MouseEvent};
use futures::{FutureExt, future::BoxFuture};
use ratatui::{layout::*, prelude::*, widgets::*};
use reqwest::{Client, ClientBuilder};
use serde::Deserialize;
use std::{
    io,
    num::NonZero,
    sync::{
        Arc,
        atomic::{AtomicUsize, Ordering},
    },
    time::Duration,
};
use tokio::sync::Mutex;

#[allow(unused)]
#[derive(Deserialize)]
struct CatApi {
    id: String,
    url: String,
    dice: Option<String>,
}

async fn load_image(client: Arc<Client>) -> reqwest::Result<ProcessedVideo> {
    let resp = client
        .get("http://api.thecatapi.com/v1/images/search")
        .send()
        .await?;
    let [resp] = resp.json::<[CatApi; 1]>().await?;
    let (url, bytes): (_, Vec<u8>) = if resp.dice.as_deref() == Some("gang") {
        (None, include_bytes!("../out.bmp").into())
    } else {
        let url = resp.url.as_str().to_string();
        let bytes = client.get(&url).send().await?.bytes().await?.into();
        (Some(url), bytes)
    };

    let image = image::load_from_memory(&bytes).unwrap();
    let ascii = artem::convert(
        image,
        &artem::config::ConfigBuilder::new()
            .target(artem::config::TargetType::Shell)
            .color(true)
            .target_size(NonZero::new(100).unwrap())
            .build(),
    );
    Ok(ProcessedVideo {
        content: ascii,
        url,
        width: 100,
    })
}

struct VideoWidget {
    id: usize,
    video: ProcessedVideo,
}

impl Widget for VideoWidget {
    fn render(self, area: Rect, buf: &mut Buffer) {
        let layout = Layout::default()
            .direction(Direction::Horizontal)
            .constraints([Constraint::Length(self.video.width as _)])
            .split(area);

        Paragraph::new(self.video.content.into_text().unwrap())
            .block(
                Block::default()
                    .title(match self.video.url {
                        Some(url) => {
                            format!("{} - {}", self.id, url)
                        }
                        None => {
                            format!("{}", self.id)
                        }
                    })
                    .title_alignment(Alignment::Center)
                    .borders(Borders::ALL),
            )
            .render(layout[0], buf);
    }
}

#[derive(Clone)]
struct ProcessedVideo {
    content: String,
    url: Option<String>,
    width: u32,
}

impl Default for ProcessedVideo {
    fn default() -> Self {
        Self {
            content: String::from("<loading>"),
            url: None,
            width: 60,
        }
    }
}

struct App {
    greatest_offset_loaded: AtomicUsize,
    in_progress_videos: Mutex<Vec<BoxFuture<'static, reqwest::Result<ProcessedVideo>>>>,
    completed_videos: ArcSwap<Vec<ProcessedVideo>>,
    client: Arc<reqwest::Client>,
}

impl App {
    async fn migrate(&self) {
        let mut in_progress = self.in_progress_videos.lock().await;
        let completed = futures::future::join_all(in_progress.iter_mut()).await;
        in_progress.clear();
        drop(in_progress);
        let mut completed = completed
            .into_iter()
            .map(|res| match res {
                Ok(video) => video,
                Err(e) => ProcessedVideo {
                    content: format!("error - {}", e),
                    width: 200,
                    ..Default::default()
                },
            })
            .collect();
        self.completed_videos.rcu(|videos| {
            let mut videos = Vec::clone(videos);
            videos.append(&mut completed);
            videos
        });
    }

    async fn grow(&self) {
        let in_progress = self.in_progress_videos.lock().await.len();
        let completed = self.completed_videos.load().len();

        let index = self.greatest_offset_loaded.load(Ordering::Relaxed);
        if index >= in_progress + completed {
            self.in_progress_videos
                .lock()
                .await
                .resize_with(index + 1 - in_progress - completed, || {
                    load_image(Arc::clone(&self.client)).boxed()
                });
        }
    }

    fn get_2_videos(&self, index: usize) -> [ProcessedVideo; 2] {
        self.greatest_offset_loaded
            .fetch_max(index + 1, Ordering::Relaxed);
        let videos = self.completed_videos.load();
        [
            videos.get(index).cloned().unwrap_or_default(),
            videos.get(index + 1).cloned().unwrap_or_default(),
        ]
    }
}

fn main() -> Result<(), io::Error> {
    let client = Arc::new(ClientBuilder::new().build().unwrap());
    let app = App {
        // Prepopulate
        greatest_offset_loaded: AtomicUsize::new(8),
        in_progress_videos: Mutex::new(vec![]),
        completed_videos: ArcSwap::new(Arc::new(vec![])),
        client,
    };
    let app = Arc::new(app);

    let mut terminal = ratatui::init();
    let rt = tokio::runtime::Runtime::new()?;
    let cloned = Arc::clone(&app);
    rt.spawn(async move {
        loop {
            cloned.migrate().await
        }
    });
    let cloned = Arc::clone(&app);
    rt.spawn(async move {
        loop {
            cloned.grow().await
        }
    });

    let mut offset = 0;
    'outer: loop {
        terminal.draw(|f| {
            let outer = Layout::default()
                .direction(Direction::Horizontal)
                .constraints([Constraint::Length(100)])
                .flex(Flex::Center)
                .split(f.area());

            let chunks = Layout::default()
                .direction(Direction::Vertical)
                .constraints([Constraint::Percentage(50); 2])
                .flex(Flex::Center)
                .split(outer[0]);

            let [vid1, vid2] = app.get_2_videos(offset);
            let videos = [
                VideoWidget {
                    id: offset,
                    video: vid1,
                },
                VideoWidget {
                    id: offset + 1,
                    video: vid2,
                },
            ];
            for (b, chunk) in videos.into_iter().zip(chunks.iter()) {
                f.render_widget(b, *chunk);
            }
        })?;

        if event::poll(Duration::from_millis(10))? {
            match event::read()? {
                Event::Key(KeyEvent { code, .. }) => match code {
                    KeyCode::Up => offset = offset.saturating_sub(1),
                    KeyCode::PageUp => offset = offset.saturating_sub(10),
                    KeyCode::Down => offset = offset.saturating_add(1),
                    KeyCode::PageDown => offset = offset.saturating_add(10),
                    KeyCode::Char('Q' | 'q') => break 'outer,
                    _ => (),
                },
                Event::Mouse(MouseEvent { kind, .. }) => match kind {
                    event::MouseEventKind::ScrollUp => offset = offset.saturating_sub(1),
                    event::MouseEventKind::ScrollDown => offset = offset.saturating_add(1),
                    _ => (),
                },
                _ => {}
            }
        }
    }
    ratatui::restore();
    Ok(())
}
