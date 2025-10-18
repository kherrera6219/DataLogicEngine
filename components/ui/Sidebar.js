import React from 'react';
import { makeStyles, shorthands, Text, mergeClasses } from '@fluentui/react-components';

const useStyles = makeStyles({
  sidebar: {
    display: 'flex',
    flexDirection: 'column',
    width: '320px',
    height: '100%',
    backgroundColor: 'var(--colorNeutralBackground3)',
    ...shorthands.borderRight('1px', 'solid', 'rgba(255,255,255,0.06)'),
    transition: 'transform 0.3s ease',
    '@media(max-width: 767px)': {
      position: 'fixed',
      bottom: 0,
      left: 0,
      right: 0,
      zIndex: 1000,
      height: '60%',
      width: '100%',
      transform: 'translateY(100%)',
      boxShadow: '0 -2px 18px rgba(0, 0, 0, 0.25)',
      ...shorthands.borderRight('0'),
      ...shorthands.borderTop('1px', 'solid', 'rgba(255,255,255,0.06)'),
    },
  },
  sidebarShow: {
    transform: 'translateY(0)',
  },
  header: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    ...shorthands.padding('20px'),
    ...shorthands.borderBottom('1px', 'solid', 'rgba(255,255,255,0.06)'),
  },
  content: {
    flex: 1,
    overflowY: 'auto',
    ...shorthands.padding('12px', '20px'),
  },
  footer: {
    ...shorthands.padding('20px'),
    ...shorthands.borderTop('1px', 'solid', 'rgba(255,255,255,0.06)'),
  },
  listItem: {
    display: 'flex',
    alignItems: 'center',
    gap: '12px',
    ...shorthands.padding('12px', '16px'),
    ...shorthands.borderRadius('10px'),
    marginBottom: '6px',
    cursor: 'pointer',
    transition: 'background-color 0.2s ease, transform 0.2s ease',
    color: 'var(--colorNeutralForeground1)',
    ':hover': {
      backgroundColor: 'rgba(117, 172, 242, 0.12)',
      transform: 'translateX(2px)',
    },
  },
  activeItem: {
    backgroundColor: 'rgba(117, 172, 242, 0.22)',
    color: '#ffffff',
    fontWeight: 600,
  },
  icon: {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    fontSize: '18px',
    color: 'var(--colorNeutralForeground3)',
  },
  activeIcon: {
    color: 'var(--colorBrandForegroundLink)',
  },
});

const Sidebar = ({
  children,
  headerTitle = 'Sidebar',
  headerActions,
  footerContent,
  isOpen = false,
  className,
  ...props
}) => {
  const styles = useStyles();

  return (
    <div
      className={mergeClasses(styles.sidebar, isOpen && styles.sidebarShow, className)}
      {...props}
    >
      <div className={styles.header}>
        <Text weight="semibold" size={400}>
          {headerTitle}
        </Text>
        {headerActions}
      </div>

      <div className={styles.content}>{children}</div>

      {footerContent && <div className={styles.footer}>{footerContent}</div>}
    </div>
  );
};

export const SidebarItem = ({ label, icon, isActive = false, onClick, className, ...props }) => {
  const styles = useStyles();

  return (
    <div
      className={mergeClasses(styles.listItem, isActive && styles.activeItem, className)}
      onClick={onClick}
      {...props}
    >
      {icon && (
        <span className={mergeClasses(styles.icon, isActive && styles.activeIcon)}>{icon}</span>
      )}
      <Text>{label}</Text>
    </div>
  );
};

export default Sidebar;
