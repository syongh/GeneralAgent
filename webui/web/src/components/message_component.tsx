import React, { useEffect, useState, useRef} from 'react'
import {Message} from './interface';
import ImageComponent from './image_component'
import FileDownloadCompoent from './file_download'
import AudioPlayer from './audio_player'
import {Button} from 'antd'
import {get_chat_file_url} from './api'
import UIMesasge from './ui_message';


interface Props {
	message: Message;
}

const MessageComponent: React.FC<Props> = (props) => {
	const [readyPlay, setReadyPlay] = useState(false); // 输入框的内容
	const message: Message = props.message;
	const bot_id: string = message.bot_id as string;
	const chat_id: string = message.chat_id as string;
	const file_url = get_chat_file_url(bot_id, chat_id, message.file as string);
	const isImage = message.file && /\.(gif|jpe?g|tiff?|png|webp|bmp)$/i.test(message.file);
	const isAudio = message.file && /\.(mp3|wav)$/i.test(message.file);
	const isUI = message.ui && message.ui !== ''
	const isFile = message.file && !isImage && !isAudio;
	if (isUI) {
		return <UIMesasge message={message} />
	}

	if (isImage) {
		return <ImageComponent image_url={file_url} />
	}
	if (isAudio) {
		if (readyPlay) {
			return <><FileDownloadCompoent file_path={file_url} /><AudioPlayer file={file_url}/></>
		} else {
			return <><FileDownloadCompoent file_path={file_url} /><Button type='link' onClick={()=>{setReadyPlay(true)}}>下载播放</Button></>
		}
	}
	if (isFile) {
		return <FileDownloadCompoent file_path={file_url} />
	}
	return (<div style={{ whiteSpace: 'pre-wrap' }}>{message.msg}</div>)
}

export default MessageComponent;