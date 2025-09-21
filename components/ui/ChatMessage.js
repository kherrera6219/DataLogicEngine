import React from 'react';
import { makeStyles, shorthands, Text, mergeClasses } from '@fluentui/react-components';
import Avatar from './Avatar';
import { bundleIcon, Person24Filled, Person24Regular, Bot24Filled, Bot24Regular, ErrorCircle24Regular } from '@fluentui/react-icons';

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
    ...shorthands.borderRadius('16px'),
    backgroundColor: 'var(--colorNeutralBackground4)',
    color: 'var(--colorNeutralForeground1)',
    boxShadow: '0 8px 24px rgba(10, 17, 35, 0.35)',
    position: 'relative',
  },
  userTextBubble: {
    backgroundColor: 'var(--colorBrandBackground)',
    color: 'var(--colorNeutralForegroundOnBrand)',
  },
  errorTextBubble: {
    backgroundColor: 'rgba(219, 54, 77, 0.12)',
    color: '#ff8593',
    border: '1px solid rgba(255, 133, 147, 0.35)',
  },
  metadata: {
    marginTop: '6px',
    fontSize: '12px',
    color: 'var(--colorNeutralForeground3)',
  },
  '@keyframes fadeIn': {
    from: { opacity: 0, transform: 'translateY(10px)' },
    to: { opacity: 1, transform: 'translateY(0)' },
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
      backgroundColor: 'rgba(255, 255, 255, 0.08)',
      ...shorthands.padding('2px', '4px'),
      ...shorthands.borderRadius('6px'),
      fontFamily: 'monospace',
    },
    '& pre': {
      backgroundColor: 'rgba(0, 0, 0, 0.2)',
      ...shorthands.padding('12px'),
      ...shorthands.borderRadius('8px'),
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

const UserIcon = bundleIcon(Person24Filled, Person24Regular);
const BotIcon = bundleIcon(Bot24Filled, Bot24Regular);

const ChatMessage = ({
  type = 'system',
  content,
  timestamp,
  metadata,
  icon,
  ...props
}) => {
  const styles = useStyles();

  const isUser = type === 'user';
  const isError = type === 'error';
  const resolvedIcon = icon || (isUser ? <UserIcon /> : isError ? <ErrorCircle24Regular /> : <BotIcon />);

  const formattedTime = timestamp
    ? new Date(timestamp).toLocaleTimeString([], {
        hour: '2-digit',
        minute: '2-digit',
      })
    : null;

  return (
    <div
      className={mergeClasses(
        styles.message,
        isUser && styles.userMessage,
        isError && styles.errorMessage,
        !isUser && !isError && styles.systemMessage,
      )}
      {...props}
    >
      <Avatar
        icon={resolvedIcon}
        color={isUser ? 'brand' : isError ? 'danger' : 'neutral'}
        size={40}
      />

      <div className={styles.content}>
        <div
          className={mergeClasses(
            styles.textBubble,
            isUser && styles.userTextBubble,
            isError && styles.errorTextBubble,
          )}
        >
          <div className={styles.markdown} dangerouslySetInnerHTML={{ __html: content }} />
        </div>

        {(formattedTime || metadata) && (
          <div className={styles.metadata}>
            {formattedTime && (
              <Text size={100} weight="regular">
                {formattedTime}
              </Text>
            )}
            {metadata && (
              <Text size={100} weight="regular">
                {formattedTime ? ' · ' : ''}
                {metadata}
              </Text>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

export default ChatMessage;
