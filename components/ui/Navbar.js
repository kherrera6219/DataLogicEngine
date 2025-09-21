import React, { useState } from 'react';
import {
  makeStyles,
  shorthands,
  Button,
  Menu,
  MenuTrigger,
  MenuList,
  MenuItem,
  MenuPopover,
  Tooltip
} from '@fluentui/react-components';
import Link from 'next/link';
import { useRouter } from 'next/router';
import {
  bundleIcon,
  Grid24Regular,
  Grid24Filled,
  Home24Filled,
  Home24Regular,
  Comment24Regular,
  Comment24Filled,
  Info24Regular,
  Info24Filled,
  Navigation24Filled,
  Navigation24Regular
} from '@fluentui/react-icons';

const useStyles = makeStyles({
  navbar: {
    display: 'flex',
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    backgroundColor: 'var(--colorNeutralBackground2)',
    boxShadow: '0 10px 30px rgba(5, 9, 20, 0.45)',
    ...shorthands.padding('10px', '24px'),
    height: '72px',
    width: '100%',
    position: 'sticky',
    top: 0,
    zIndex: 120,
    backdropFilter: 'blur(14px)',
    borderBottom: `1px solid rgba(255, 255, 255, 0.06)`,
  },
  brand: {
    display: 'flex',
    alignItems: 'center',
    gap: '12px',
    textDecoration: 'none',
    color: 'var(--colorNeutralForeground1)',
    fontWeight: 600,
  },
  logo: {
    display: 'flex',
    fontSize: '28px',
    width: '40px',
    height: '40px',
    borderRadius: '12px',
    alignItems: 'center',
    justifyContent: 'center',
    background: 'linear-gradient(135deg, rgba(50, 116, 198, 0.85), rgba(14, 53, 103, 0.85))',
    color: '#ffffff',
  },
  title: {
    fontSize: '18px',
    letterSpacing: '0.02em',
    '@media(max-width: 576px)': {
      display: 'none',
    },
  },
  titleShort: {
    display: 'none',
    fontSize: '18px',
    '@media(max-width: 576px)': {
      display: 'block',
    },
  },
  navItems: {
    display: 'flex',
    alignItems: 'center',
    gap: '8px',
    '@media(max-width: 900px)': {
      display: 'none',
    },
  },
  mobileMenu: {
    display: 'none',
    '@media(max-width: 900px)': {
      display: 'block',
    },
  },
  navLink: {
    color: 'var(--colorNeutralForeground1)',
    textDecoration: 'none',
    ...shorthands.padding('10px', '14px'),
    borderRadius: '10px',
    transition: 'background-color 0.25s, color 0.25s',
    display: 'inline-flex',
    alignItems: 'center',
    gap: '8px',
    fontWeight: 500,
    ':hover': {
      backgroundColor: 'rgba(117, 172, 242, 0.18)',
      color: '#dce9ff',
    },
  },
  activeNavLink: {
    backgroundColor: 'rgba(117, 172, 242, 0.28)',
    color: '#ffffff',
    fontWeight: 600,
  },
  navIcon: {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
  }
});

const HomeIcon = bundleIcon(Home24Filled, Home24Regular);
const ChatIcon = bundleIcon(Comment24Filled, Comment24Regular);
const InfoIcon = bundleIcon(Info24Filled, Info24Regular);
const GridIcon = bundleIcon(Grid24Filled, Grid24Regular);
const MenuIcon = bundleIcon(Navigation24Filled, Navigation24Regular);

const Navbar = ({ navItems = [] }) => {
  const styles = useStyles();
  const router = useRouter();
  const [isOpen, setIsOpen] = useState(false);

  const isActiveLink = (path) => router.pathname === path;

  return (
    <nav className={styles.navbar}>
      <Link href="/" className={styles.brand}>
        <span className={styles.logo}>
          <GridIcon fontSize={20} />
        </span>
        <span className={styles.title}>Universal Knowledge Graph</span>
        <span className={styles.titleShort}>UKG</span>
      </Link>

      <div className={styles.navItems}>
        {navItems.map((item) => (
          <Tooltip content={item.label} key={item.href} relationship="label">
            <Link
              href={item.href}
              className={`${styles.navLink} ${isActiveLink(item.href) ? styles.activeNavLink : ''}`}
            >
              {item.icon && <span className={styles.navIcon}>{item.icon}</span>}
              {item.label}
            </Link>
          </Tooltip>
        ))}
      </div>

      <div className={styles.mobileMenu}>
        <Menu open={isOpen} onOpenChange={(e, data) => setIsOpen(data.open)}>
          <MenuTrigger disableButtonEnhancement>
            <Button
              icon={<MenuIcon />}
              appearance="transparent"
              aria-label="Open navigation menu"
            />
          </MenuTrigger>
          <MenuPopover>
            <MenuList>
              {navItems.map((item) => (
                <MenuItem
                  key={item.href}
                  onClick={() => {
                    setIsOpen(false);
                    router.push(item.href);
                  }}
                  icon={item.icon}
                >
                  {item.label}
                </MenuItem>
              ))}
            </MenuList>
          </MenuPopover>
        </Menu>
      </div>
    </nav>
  );
};

Navbar.defaultProps = {
  navItems: [
    { href: '/', label: 'Home', icon: <HomeIcon /> },
    { href: '/chat', label: 'Chat', icon: <ChatIcon /> },
    { href: '/knowledge-graph', label: 'Knowledge Graph', icon: <GridIcon /> },
    { href: '/contextual', label: 'Context Experts', icon: <InfoIcon /> },
  ],
};

export default Navbar;
