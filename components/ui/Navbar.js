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

const useStyles = makeStyles({
  navbar: {
    display: 'flex',
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    backgroundColor: 'var(--colorNeutralBackground1)',
    boxShadow: '0 2px 4px rgba(0, 0, 0, 0.1)',
    ...shorthands.padding('8px', '16px'),
    height: '60px',
    width: '100%',
    position: 'sticky',
    top: 0,
    zIndex: 100,
  },
  brand: {
    display: 'flex',
    alignItems: 'center',
    gap: '12px',
    textDecoration: 'none',
    color: 'var(--colorBrandForeground1)',
    fontWeight: 600,
  },
  logo: {
    display: 'flex',
    fontSize: '24px',
  },
  title: {
    fontSize: '18px',
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
    '@media(max-width: 768px)': {
      display: 'none',
    },
  },
  mobileMenu: {
    display: 'none',
    '@media(max-width: 768px)': {
      display: 'block',
    },
  },
  navLink: {
    color: 'var(--colorNeutralForeground1)',
    textDecoration: 'none',
    ...shorthands.padding('8px', '12px'),
    borderRadius: '4px',
    transition: 'background-color 0.2s',
    ':hover': {
      backgroundColor: 'var(--colorNeutralBackground2)',
    },
  },
  activeNavLink: {
    backgroundColor: 'var(--colorNeutralBackground2)',
    fontWeight: 600,
  },
});

const Navbar = ({ navItems = [] }) => {
  const styles = useStyles();
  const router = useRouter();
  const [isOpen, setIsOpen] = useState(false);

  const isActiveLink = (path) => router.pathname === path;

  return (
    <nav className={styles.navbar}>
      <Link href="/" className={styles.brand}>
        <span className={styles.logo}><i className="bi bi-diagram-3"></i></span>
        <span className={styles.title}>Universal Knowledge Graph</span>
        <span className={styles.titleShort}>UKG</span>
      </Link>

      <div className={styles.navItems}>
        {navItems.map((item, index) => (
          <Tooltip content={item.label} key={index}>
            <Link 
              href={item.href} 
              className={`${styles.navLink} ${isActiveLink(item.href) ? styles.activeNavLink : ''}`}
            >
              {item.icon && <i className={`bi bi-${item.icon} me-2`}></i>}
              {item.label}
            </Link>
          </Tooltip>
        ))}
      </div>

      <div className={styles.mobileMenu}>
        <Menu>
          <MenuTrigger disableButtonEnhancement>
            <Button 
              icon={<i className="bi bi-list"></i>}
              iconOnly
              appearance="subtle"
              aria-label="Menu"
            />
          </MenuTrigger>
          <MenuPopover>
            <MenuList>
              {navItems.map((item, index) => (
                <MenuItem 
                  key={index} 
                  onClick={() => router.push(item.href)}
                  icon={<i className={`bi bi-${item.icon}`}></i>}
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
    { href: '/', label: 'Home', icon: 'house' },
    { href: '/axis1', label: 'Axis 1', icon: '1-circle' },
    { href: '/axis2', label: 'Axis 2', icon: '2-circle' },
    { href: '/axis3', label: 'Axis 3', icon: '3-circle' },
    { href: '/axis4', label: 'Axis 4', icon: '4-circle' },
    { href: '/axis5', label: 'Axis 5', icon: '5-circle' },
    { href: '/axis6', label: 'Axis 6', icon: 'gear' },
    { href: '/compliance', label: 'Compliance', icon: 'check-circle' }
  ],
};

export default Navbar;