
import React, { useEffect } from 'react';
import { makeStyles, shorthands, Text, Button, mergeClasses } from '@fluentui/react-components';
import Link from 'next/link';
import { useRouter } from 'next/router';
import Navbar from './ui/Navbar';

const useStyles = makeStyles({
  container: {
    display: 'flex',
    flexDirection: 'column',
    minHeight: '100vh',
  },
  main: {
    flex: '1 0 auto',
    ...shorthands.padding('24px', '0'),
    width: '100%',
    maxWidth: '100%',
    overflowX: 'hidden',
  },
  mainContent: {
    maxWidth: '1400px',
    marginLeft: 'auto',
    marginRight: 'auto',
    ...shorthands.padding('0', '16px'),
    '@media(min-width: 576px)': {
      ...shorthands.padding('0', '24px'),
    },
  },
  footer: {
    backgroundColor: 'var(--colorNeutralBackground2)',
    color: 'var(--colorNeutralForeground2)',
    ...shorthands.padding('16px', '0'),
    marginTop: '32px',
  },
  footerContent: {
    maxWidth: '1400px',
    marginLeft: 'auto',
    marginRight: 'auto',
    ...shorthands.padding('0', '16px'),
    '@media(min-width: 576px)': {
      ...shorthands.padding('0', '24px'),
    },
  },
  footerRow: {
    display: 'flex',
    flexDirection: 'column',
    '@media(min-width: 768px)': {
      flexDirection: 'row',
      alignItems: 'center',
      justifyContent: 'space-between',
    },
  },
  footerCopyright: {
    textAlign: 'center',
    marginBottom: '16px',
    '@media(min-width: 768px)': {
      textAlign: 'left',
      marginBottom: '0',
    },
  },
  socialLinks: {
    display: 'flex',
    justifyContent: 'center',
    gap: '24px',
    '@media(min-width: 768px)': {
      justifyContent: 'flex-end',
    },
  },
  socialLink: {
    color: 'var(--colorNeutralForeground2)',
    fontSize: '20px',
    transition: 'color 0.2s',
    ':hover': {
      color: 'var(--colorBrandForeground1)',
    },
  },
});

export default function Layout({ children, className }) {
  const styles = useStyles();
  const router = useRouter();

  const navItems = [
    { label: 'Home', href: '/', icon: 'house-door' },
    { label: 'Chat', href: '/chat', icon: 'chat-dots' },
    { label: 'About', href: '#about', icon: 'info-circle' },
  ];

  return (
    <div className={styles.container}>
      <Navbar navItems={navItems} />
      
      <main className={mergeClasses(styles.main, className)}>
        <div className={styles.mainContent}>
          {children}
        </div>
      </main>
      
      <footer className={styles.footer}>
        <div className={styles.footerContent}>
          <div className={styles.footerRow}>
            <div className={styles.footerCopyright}>
              <Text size={200}>Universal Knowledge Graph System &copy; {new Date().getFullYear()}</Text>
            </div>
            
            <div className={styles.socialLinks}>
              <a href="#" className={styles.socialLink} aria-label="GitHub">
                <i className="bi bi-github"></i>
              </a>
              <a href="#" className={styles.socialLink} aria-label="Twitter">
                <i className="bi bi-twitter"></i>
              </a>
              <a href="#" className={styles.socialLink} aria-label="LinkedIn">
                <i className="bi bi-linkedin"></i>
              </a>
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
}
