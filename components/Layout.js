import React from 'react';
import { makeStyles, shorthands, Text, mergeClasses } from '@fluentui/react-components';
import Navbar from './ui/Navbar';
import {
  bundleIcon,
  Home24Filled,
  Home24Regular,
  ChatSparkle24Filled,
  ChatSparkle24Regular,
  Branch24Filled,
  Branch24Regular,
  Info24Filled,
  Info24Regular,
  BookDatabase24Filled,
  BookDatabase24Regular,
  PeopleCommunity24Filled,
  PeopleCommunity24Regular,
  ShieldGlobe24Filled,
  ShieldGlobe24Regular,
  Share24Filled,
  Share24Regular,
  Link24Regular,
  Open24Regular,
  Globe24Regular
} from '@fluentui/react-icons';

const useStyles = makeStyles({
  container: {
    display: 'flex',
    flexDirection: 'column',
    minHeight: '100vh',
    background: 'radial-gradient(circle at top left, rgba(50,116,198,0.18), transparent 45%)',
  },
  main: {
    flex: '1 0 auto',
    ...shorthands.padding('48px', '0'),
    width: '100%',
    maxWidth: '100%',
    overflowX: 'hidden',
  },
  mainContent: {
    maxWidth: 'var(--page-max-width)',
    marginLeft: 'auto',
    marginRight: 'auto',
    ...shorthands.padding('0', '24px'),
    '@media(min-width: 1200px)': {
      ...shorthands.padding('0', '32px'),
    },
  },
  footer: {
    backgroundColor: 'var(--colorNeutralBackground2)',
    color: 'var(--colorNeutralForeground2)',
    ...shorthands.padding('24px', '0'),
    borderTop: '1px solid rgba(255,255,255,0.04)',
  },
  footerContent: {
    maxWidth: 'var(--page-max-width)',
    marginLeft: 'auto',
    marginRight: 'auto',
    ...shorthands.padding('0', '24px'),
  },
  footerRow: {
    display: 'flex',
    flexDirection: 'column',
    gap: '16px',
    '@media(min-width: 768px)': {
      flexDirection: 'row',
      alignItems: 'center',
      justifyContent: 'space-between',
    },
  },
  socialLinks: {
    display: 'flex',
    justifyContent: 'center',
    gap: '20px',
    '@media(min-width: 768px)': {
      justifyContent: 'flex-end',
    },
  },
  socialLink: {
    color: 'var(--colorNeutralForeground2)',
    fontSize: '22px',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    width: '40px',
    height: '40px',
    borderRadius: '12px',
    backgroundColor: 'rgba(255,255,255,0.04)',
    transition: 'all 0.2s ease',
    ':hover': {
      color: '#ffffff',
      backgroundColor: 'rgba(117, 172, 242, 0.35)',
    },
  },
});

const HomeIcon = bundleIcon(Home24Filled, Home24Regular);
const ChatIcon = bundleIcon(ChatSparkle24Filled, ChatSparkle24Regular);
const KnowledgeIcon = bundleIcon(BookDatabase24Filled, BookDatabase24Regular);
const BranchIcon = bundleIcon(Branch24Filled, Branch24Regular);
const PeopleIcon = bundleIcon(PeopleCommunity24Filled, PeopleCommunity24Regular);
const InfoIcon = bundleIcon(Info24Filled, Info24Regular);
const ComplianceIcon = bundleIcon(ShieldGlobe24Filled, ShieldGlobe24Regular);
const ShareIcon = bundleIcon(Share24Filled, Share24Regular);

export default function Layout({ children, className }) {
  const styles = useStyles();

  const navItems = [
    { label: 'Home', href: '/', icon: <HomeIcon /> },
    { label: 'Chat', href: '/chat', icon: <ChatIcon /> },
    { label: 'Knowledge Graph', href: '/knowledge-graph', icon: <KnowledgeIcon /> },
    { label: 'Pillars', href: '/pillars', icon: <BranchIcon /> },
    { label: 'Context Experts', href: '/contextual', icon: <PeopleIcon /> },
    { label: 'Compliance', href: '/compliance-dashboard', icon: <ComplianceIcon /> },
    { label: 'Resources', href: '/unified-mapping', icon: <ShareIcon /> },
    { label: 'About', href: '/regulatory', icon: <InfoIcon /> },
  ];

  return (
    <div className={styles.container}>
      <Navbar navItems={navItems} />

      <main className={mergeClasses(styles.main, className)}>
        <div className={styles.mainContent}>{children}</div>
      </main>

      <footer className={styles.footer}>
        <div className={styles.footerContent}>
          <div className={styles.footerRow}>
            <Text size={200} weight="semibold">
              Universal Knowledge Graph System &copy; {new Date().getFullYear()}
            </Text>

            <div className={styles.socialLinks}>
              <a href="https://github.com" className={styles.socialLink} aria-label="Open Source">
                <Open24Regular />
              </a>
              <a href="https://www.linkedin.com" className={styles.socialLink} aria-label="LinkedIn">
                <Link24Regular />
              </a>
              <a href="https://www.microsoft.com" className={styles.socialLink} aria-label="Microsoft">
                <Globe24Regular />
              </a>
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
}
