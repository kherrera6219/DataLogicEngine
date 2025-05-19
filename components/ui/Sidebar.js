
import React from 'react';
import { 
  makeStyles, 
  shorthands,
  Button,
  Text,
  Divider,
  mergeClasses
} from '@fluentui/react-components';

const useStyles = makeStyles({
  sidebar: {
    display: 'flex',
    flexDirection: 'column',
    width: '280px',
    height: '100%',
    backgroundColor: 'var(--colorNeutralBackground2)',
    ...shorthands.borderRight('1px', 'solid', 'var(--colorNeutralStroke2)'),
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
      boxShadow: '0 -2px 10px rgba(0, 0, 0, 0.2)',
      ...shorthands.borderRight('0'),
      ...shorthands.borderTop('1px', 'solid', 'var(--colorNeutralStroke2)'),
    },
  },
  sidebarShow: {
    transform: 'translateY(0)',
  },
  header: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    ...shorthands.padding('16px'),
    ...shorthands.borderBottom('1px', 'solid', 'var(--colorNeutralStroke2)'),
  },
  content: {
    flex: 1,
    overflowY: 'auto',
    ...shorthands.padding('8px'),
  },
  footer: {
    ...shorthands.padding('16px'),
    ...shorthands.borderTop('1px', 'solid', 'var(--colorNeutralStroke2)'),
  },
  listItem: {
    display: 'flex',
    alignItems: 'center',
    gap: '12px',
    ...shorthands.padding('12px'),
    ...shorthands.borderRadius('4px'),
    marginBottom: '4px',
    cursor: 'pointer',
    transition: 'background-color 0.2s',
    ':hover': {
      backgroundColor: 'var(--colorNeutralBackground3)',
    },
    color: 'var(--colorNeutralForeground1)',
    textOverflow: 'ellipsis',
    overflow: 'hidden',
    whiteSpace: 'nowrap',
  },
  activeItem: {
    backgroundColor: 'var(--colorBrandBackground2)',
    fontWeight: 600,
    ':hover': {
      backgroundColor: 'var(--colorBrandBackground2Hover)',
    },
  },
  icon: {
    fontSize: '16px',
    color: 'var(--colorNeutralForeground3)',
  },
  activeIcon: {
    color: 'var(--colorBrandForeground1)',
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
      className={mergeClasses(
        styles.sidebar, 
        isOpen && styles.sidebarShow,
        className
      )} 
      {...props}
    >
      <div className={styles.header}>
        <Text weight="semibold" size={400}>{headerTitle}</Text>
        {headerActions}
      </div>
      
      <div className={styles.content}>
        {children}
      </div>
      
      {footerContent && (
        <div className={styles.footer}>
          {footerContent}
        </div>
      )}
    </div>
  );
};

// Helper component for sidebar items
export const SidebarItem = ({ 
  label, 
  icon, 
  isActive = false, 
  onClick,
  ...props 
}) => {
  const styles = useStyles();
  
  return (
    <div 
      className={mergeClasses(
        styles.listItem, 
        isActive && styles.activeItem
      )}
      onClick={onClick}
      {...props}
    >
      {icon && (
        <i className={mergeClasses(
          `bi bi-${icon}`, 
          styles.icon,
          isActive && styles.activeIcon
        )}></i>
      )}
      <Text>{label}</Text>
    </div>
  );
};

export default Sidebar;
