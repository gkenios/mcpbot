import type { FC } from "react";
import { marked } from "marked";
import DOMPurify from "dompurify";

import { MessageItem, Role } from "../backend"
import { BotIcon, Spinner } from "./icons";

interface MessageProps {
  chat: Partial<MessageItem>;
}

// Custom renderer to handle links in markdown
const renderer = new marked.Renderer();
renderer.link = function ({ href, title, text }) {
  const titleAttr = title ? ` title="${title}"` : "";
  return `<a href="${href}" target="_blank" rel="noopener noreferrer"${titleAttr}>${text}</a>`;
};
marked.setOptions({ renderer });

const Message: FC<MessageProps> = ({ chat }) => {
  const getMarkdownAsHtml = (markdown: string = "") => {
    const rawHtml = marked.parse(markdown) as string;
    const cleanHtml = DOMPurify.sanitize(rawHtml.trim(), {
      ADD_ATTR: ['target', 'rel'] // Just to ensure these aren't stripped
    });
    return { __html: cleanHtml };
  };

  if (chat.role === Role.Human) {
    return (
      <div className={`message ${chat.role}-message`}>
        <p className="message-text">{chat.text}</p>
      </div>
    );
  } else if (chat.role === Role.AI) {
    return (
      <div className={`message ${chat.role}-message`}>
        <BotIcon />
        <div className="message-text">
          {
            chat.text === "__loading__"
            ? <Spinner />
            : <div dangerouslySetInnerHTML={getMarkdownAsHtml(chat.text)} />
          }
        </div>
      </div>
    );
  }

  return null; // fallback
};

export default Message;
