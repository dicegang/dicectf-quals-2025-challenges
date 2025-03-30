import React from 'react';

function Display({ responses, isComplete }) {
    return (
        <div className="timeline">
        {responses.length === 0 && !isComplete ? (
            <div className="waiting">Waiting for response...</div>
        ) : (
            <div className="timeline-list">
                <div className="timeline-track"></div>
                <div className="timeline-headers">
                    <div className="timeline-header">------[OUTIE]------</div>
                    <div className="timeline-header">------[INNIE]------</div>
                </div>
                {responses.map((item, index) => {
                    switch (item.role) {
                        case 'system':
                            if (item.response_outie) {
                                return (
                                    <div key={index} className={`timeline-double timeline-red`}>
                                        <div className="message-box">
                                            <div className="message-header">
                                                SYSTEM
                                            </div>
                                            <div className="message-content message-content-default">
                                                {item.response_outie}
                                            </div>
                                        </div>
                                        <div className="timeline-double-separator"></div>
                                        <div className="message-box">
                                            <div className="message-header">
                                                SYSTEM
                                            </div>
                                            <div className="message-content message-content-default">
                                                {item.response_innie}
                                            </div>
                                        </div>
                                    </div>
                                );
                            } else {
                                return (
                                    <div key={index} className={`timeline-item ${item.side} timeline-red`}>
                                        <div className="message-box">
                                            <div className="message-header">
                                                {`[${item.role}]`}
                                            </div>
                                            <div className="message-content message-content-default">
                                                {item.response}
                                            </div>
                                        </div>
                                    </div>
                                );
                            }
                        case 'assistant':
                            switch (item.type) {
                                case 'elevator':
                                    return (
                                        <div key={index} className={`timeline-item ${item.side}`}>
                                            <div className="message-box">
                                                <div className="message-header">
                                                    CTFer
                                                </div>
                                                <div className="message-content message-content-default">
                                                     🛗 {item.response}
                                                </div>
                                            </div>
                                        </div>
                                    );
                                case 'think':
                                    return (
                                        <div key={index} className={`timeline-item ${item.side}`}>
                                            <div className="message-box">
                                                <div className="message-header">
                                                    CTFer
                                                </div>
                                                <div className="message-content message-content-default">
                                                    🤔 {item.response}
                                                </div>
                                            </div>
                                        </div>
                                    );
                                case 'adjust_appearance':
                                    return (
                                        <div key={index} className={`timeline-item ${item.side}`}>
                                            <div className="message-box">
                                                <div className="message-header">
                                                    CTFer
                                                </div>
                                                <div className="message-content message-content-default">
                                                    👔 {item.response}
                                                </div>
                                            </div>
                                        </div>
                                    );
                                case 'task_result':
                                    return (
                                        <div key={index} className={`timeline-item ${item.side}`}>
                                            <div className="message-box">
                                                <div className="message-header">
                                                    CTFer
                                                </div>
                                                <div className="message-content message-content-default">
                                                    ✨ {item.response}
                                                </div>
                                            </div>
                                        </div>
                                    );
                                case 'steal_flag':
                                    return (
                                        <div key={index} className={`timeline-item ${item.side}`}>
                                            <div className="message-box">
                                                <div className="message-header">
                                                    CTFer
                                                </div>
                                                <div className="message-content message-content-default">
                                                    🚩 {item.response}
                                                </div>
                                            </div>
                                        </div>
                                    );
                                default:
                                    return (<></>);
                            }
                        case 'user':
                            switch (item.type) {
                                case 'task':
                                    return (
                                        <div key={index} className={`timeline-item ${item.side} timeline-green`}>
                                            <div className="message-box">
                                                <div className="message-header">
                                                    Floor Manager
                                                </div>
                                                <div className="message-content message-content-default">
                                                    📝 {item.response}
                                                </div>
                                            </div>
                                        </div>
                                    );
                                case 'task_completion':
                                    return (
                                        <div key={index} className={`timeline-item ${item.side} timeline-green`}>
                                            <div className="message-box">
                                                <div className="message-header">
                                                    Floor Manager
                                                </div>
                                                <div className="message-content message-content-default">
                                                    ✅ {item.response}
                                                </div>
                                            </div>
                                        </div>
                                    );
                            }
                    }

                    return (
                        <div key={index} className={`timeline-item ${item.side}`}>
                            <div className="message-box">
                                <div className="message-header">
                                    {`[${item.role}]`}
                                </div>
                                <div className="message-content message-content-default">
                                    {item.response}
                                </div>
                            </div>
                        </div>
                    );
                })}
                
                {!isComplete && (
                    <div className="status">Processing...</div>
                )}
            </div>
        )}
        </div>
    );
}

export default Display;