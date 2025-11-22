
import React from 'react';
import {
  makeStyles,
  shorthands,
  Text,
  mergeClasses
} from '@fluentui/react-components';
import DOMPurify from 'isomorphic-dompurify';
import Avatar from './Avatar';

const useStyles = makeStyles({
  message: {
    display: 'flex',
    marginBottom: '24px',
    gap: '16px',
    maxWidth: '85%',
    animation: 'fadeIn 0.3s ease-in-out',
  },
  userMessage: {
    alignSelf: 'flex-end',
    flexDirection: 'row-reverse',
    marginLeft: 'auto',
  },
  systemMessage: {
    alignSelf: 'flex-start',
  },
  errorMessage: {
    alignSelf: 'flex-start',
  },
  content: {
    maxWidth: '100%',
  },
  textBubble: {
    ...shorthands.padding('16px'),
    ...shorthands.borderRadius('12px', '12px', '12px', '0'),
    backgroundColor: 'var(--colorNeutralBackground4)',
    color: 'var(--colorNeutralForeground1)',
    boxShadow: '0 2px 5px rgba(0, 0, 0, 0.1)',
    position: 'relative',
  },
  userTextBubble: {
    backgroundColor: 'var(--colorBrandBackground)',
    color: 'var(--colorNeutralForegroundInverted)',
    ...shorthands.borderRadius('12px', '12px', '0', '12px'),
  },
  errorTextBubble: {
    backgroundColor: 'var(--colorPaletteRedBackground2)',
    color: 'var(--colorPaletteRedForeground2)',
    ...shorthands.borderRadius('12px', '12px', '12px', '0'),
  },
  metadata: {
    marginTop: '4px',
    fontSize: '12px',
    color: 'var(--colorNeutralForeground3)',
  },
  '@keyframes fadeIn': {
    from: { opacity: 0, transform: 'translateY(10px)' },
    to: { opacity: 1, transform: 'translateY(0)' }
  },
  markdown: {
    lineHeight: 1.6,
    '& h1, & h2, & h3, & h4, & h5, & h6': {
      margin: '16px 0 8px',
    },
    '& h1': {
      fontSize: '1.8rem',
    },
    '& h2': {
      fontSize: '1.5rem',
    },
    '& h3': {
      fontSize: '1.3rem',
    },
    '& p': {
      margin: '8px 0',
    },
    '& ul, & ol': {
      marginLeft: '20px',
    },
    '& code': {
      backgroundColor: 'rgba(0, 0, 0, 0.1)',
      ...shorthands.padding('2px', '4px'),
      ...shorthands.borderRadius('4px'),
      fontFamily: 'monospace',
    },
    '& pre': {
      backgroundColor: 'rgba(0, 0, 0, 0.1)',
      ...shorthands.padding('12px'),
      ...shorthands.borderRadius('4px'),
      overflowX: 'auto',
    },
    '& a': {
      color: 'var(--colorBrandForegroundLink)',
      textDecoration: 'none',
      ':hover': {
        textDecoration: 'underline',
      },
    },
  },
});

const ChatMessage = ({
  type = 'system',  // 'system', 'user', 'error'
  content,
  timestamp,
  avatarIcon = '',
  avatarInitials = '',
  avatarImage = '',
  metadata,
  ...props
}) => {
  const styles = useStyles();

  const isUser = type === 'user';
  const isError = type === 'error';

  const formattedTime = new Date(timestamp).toLocaleTimeString([], {
    hour: '2-digit',
    minute: '2-digit'
  });

  // Sanitize HTML content to prevent XSS attacks
  const sanitizedContent = DOMPurify.sanitize(content, {
    ALLOWED_TAGS: ['h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'p', 'ul', 'ol', 'li', 'code', 'pre', 'a', 'strong', 'em', 'br'],
    ALLOWED_ATTR: ['href', 'target', 'rel']
  });
  
  return (
    <div 
      className={mergeClasses(
        styles.message,
        isUser && styles.userMessage,
        isError && styles.errorMessage,
        !isUser && !isError && styles.systemMessage
      )}
      {...props}
    >
      <Avatar 
        icon={avatarIcon || (isUser ? 'person' : isError ? 'exclamation-triangle' : 'robot')}
        initials={avatarInitials}
        image={avatarImage}
        color={isUser ? 'brand' : isError ? 'danger' : 'neutral'}
      />
      
      <div className={styles.content}>
        <div
          className={mergeClasses(
            styles.textBubble,
            isUser && styles.userTextBubble,
            isError && styles.errorTextBubble
          )}
        >
          <div className={styles.markdown} dangerouslySetInnerHTML={{ __html: sanitizedContent }} />
        </div>
        
        <div className={styles.metadata}>
          {timestamp && (
            <Text size={100} weight="regular">{formattedTime}</Text>
          )}
          {metadata && (
            <Text size={100} weight="regular"> · {metadata}</Text>
          )}
        </div>
      </div>
    </div>
  );
};

export default ChatMessage;
