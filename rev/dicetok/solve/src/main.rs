use warp::Filter;

#[tokio::main]
async fn main() {
    let route = warp::path!("v1" / "images" / "search")
        .and(warp::get())
        .and_then(handle_request);

    warp::serve(route).run(([0, 0, 0, 0], 80)).await;
}

async fn handle_request() -> Result<impl warp::Reply, warp::Rejection> {
    let mut cat = serde_json::Map::new();
    cat.insert("id".to_string(), "XXX".into());
    cat.insert("url".to_string(), "YYY".into());
    cat.insert("dice".to_string(), "gang".into());
    Ok(warp::reply::json(&[cat]))
}
