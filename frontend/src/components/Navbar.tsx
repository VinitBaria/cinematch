import React, { useEffect, useRef, useState } from 'react';
import { Link, NavLink, useLocation, useNavigate } from 'react-router-dom';
import { Search, Bell, ChevronDown, LogOut, Menu, X, Star, Sparkles, Film } from 'lucide-react';
import { useAuth } from '../context/AuthContext';

const NAV_LINKS = [
  { name: 'Home', path: '/' },
  { name: 'AI Picks', path: '/recommendations' },
  { name: 'Browse', path: '/search' },
  { name: 'My Ratings', path: '/ratings' },
];

export const Navbar: React.FC = () => {
  const { user, isAuthenticated, logout } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();

  const [scrolled, setScrolled] = useState(false);
  const [searchOpen, setSearchOpen] = useState(false);
  const [query, setQuery] = useState('');
  const [mobileOpen, setMobileOpen] = useState(false);
  const [menuOpen, setMenuOpen] = useState(false);

  const searchInput = useRef<HTMLInputElement>(null);
  const menuRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 24);
    onScroll();
    window.addEventListener('scroll', onScroll, { passive: true });
    return () => window.removeEventListener('scroll', onScroll);
  }, []);

  // Close menus on route change
  useEffect(() => {
    setMobileOpen(false);
    setMenuOpen(false);
  }, [location.pathname]);

  // Click-outside for profile menu
  useEffect(() => {
    if (!menuOpen) return;
    const onDown = (e: MouseEvent) => {
      if (menuRef.current && !menuRef.current.contains(e.target as Node)) setMenuOpen(false);
    };
    document.addEventListener('mousedown', onDown);
    return () => document.removeEventListener('mousedown', onDown);
  }, [menuOpen]);

  useEffect(() => {
    if (searchOpen) searchInput.current?.focus();
  }, [searchOpen]);

  const submitSearch = (e: React.FormEvent) => {
    e.preventDefault();
    if (query.trim()) {
      navigate(`/search?q=${encodeURIComponent(query.trim())}`);
      setSearchOpen(false);
      setMobileOpen(false);
    }
  };

  return (
    <header
      className={`fixed inset-x-0 top-0 z-50 transition-all duration-500 ${
        scrolled || mobileOpen
          ? 'bg-[#141414]/95 shadow-[0_8px_30px_rgba(0,0,0,0.6)] backdrop-blur-md'
          : 'bg-gradient-to-b from-black/80 via-black/30 to-transparent'
      }`}
    >
      <nav className="mx-auto flex h-16 max-w-[1800px] items-center justify-between px-4 md:h-[68px] md:px-12">
        {/* Left */}
        <div className="flex items-center gap-8">
          <Link to="/" className="group flex items-center gap-2" aria-label="CineMatch AI home">
            <Film className="h-6 w-6 text-[#e50914] transition-transform duration-500 group-hover:rotate-[20deg]" />
            <span className="font-display text-[28px] leading-none tracking-wider text-[#e50914] transition-all group-hover:drop-shadow-[0_0_14px_rgba(229,9,20,0.7)] md:text-[32px]">
              CINEMATCH
            </span>
            <span className="rounded bg-white px-1 py-px text-[10px] font-black leading-none text-black">AI</span>
          </Link>

          <ul className="hidden items-center gap-6 md:flex">
            {NAV_LINKS.map((link) => (
              <li key={link.path}>
                <NavLink
                  to={link.path}
                  end={link.path === '/'}
                  className={({ isActive }) =>
                    `group/link relative py-1 text-sm transition-colors duration-200 ${
                      isActive ? 'font-bold text-white' : 'font-medium text-zinc-300 hover:text-white'
                    }`
                  }
                >
                  {({ isActive }) => (
                    <>
                      {link.name}
                      <span
                        className={`absolute -bottom-0.5 left-0 h-0.5 w-full origin-left rounded-full bg-[#e50914] transition-transform duration-300 ${
                          isActive ? 'scale-x-100' : 'scale-x-0 group-hover/link:scale-x-100'
                        }`}
                      />
                    </>
                  )}
                </NavLink>
              </li>
            ))}
          </ul>
        </div>

        {/* Right */}
        <div className="flex items-center gap-2 md:gap-4">
          {/* Expanding search */}
          <form
            onSubmit={submitSearch}
            className={`hidden items-center overflow-hidden rounded-md border transition-all duration-500 ease-out sm:flex ${
              searchOpen
                ? 'w-64 border-white/70 bg-black/80 pl-2'
                : 'w-10 border-transparent bg-transparent'
            }`}
          >
            <button
              type={searchOpen && query ? 'submit' : 'button'}
              onClick={() => !searchOpen && setSearchOpen(true)}
              aria-label="Search"
              className="flex h-10 w-8 flex-shrink-0 items-center justify-center text-white"
            >
              <Search className="h-5 w-5" />
            </button>
            <input
              ref={searchInput}
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              onBlur={() => !query && setSearchOpen(false)}
              onKeyDown={(e) => e.key === 'Escape' && (setSearchOpen(false), setQuery(''))}
              placeholder="Titles, genres…"
              tabIndex={searchOpen ? 0 : -1}
              className="h-10 w-full bg-transparent px-2 text-sm text-white placeholder-zinc-500 outline-none"
            />
          </form>

          {/* Mobile search shortcut */}
          <Link to="/search" className="p-2 text-white sm:hidden" aria-label="Search">
            <Search className="h-5 w-5" />
          </Link>

          {isAuthenticated && user ? (
            <>
              <button className="hidden p-2 text-white transition-transform hover:scale-110 md:block" aria-label="Notifications">
                <Bell className="h-5 w-5" />
              </button>

              <div className="relative" ref={menuRef}>
                <button
                  onClick={() => setMenuOpen((o) => !o)}
                  aria-haspopup="menu"
                  aria-expanded={menuOpen}
                  className="flex items-center gap-2"
                >
                  <span className="flex h-8 w-8 items-center justify-center rounded-md bg-gradient-to-br from-[#e50914] to-[#7a0309] text-sm font-black uppercase text-white shadow-lg ring-1 ring-white/20 transition-transform hover:scale-105">
                    {user.name.charAt(0)}
                  </span>
                  <ChevronDown
                    className={`hidden h-4 w-4 text-white transition-transform duration-300 sm:block ${
                      menuOpen ? 'rotate-180' : ''
                    }`}
                  />
                </button>

                {menuOpen && (
                  <div
                    role="menu"
                    className="absolute right-0 mt-3 w-64 origin-top-right overflow-hidden rounded-lg bg-[#181818]/98 shadow-2xl ring-1 ring-white/10 backdrop-blur-xl animate-fade-down"
                  >
                    <div className="flex items-center gap-3 border-b border-white/10 p-4">
                      <span className="flex h-10 w-10 items-center justify-center rounded-md bg-gradient-to-br from-[#e50914] to-[#7a0309] font-black uppercase">
                        {user.name.charAt(0)}
                      </span>
                      <div className="min-w-0">
                        <p className="truncate text-sm font-bold text-white">{user.name}</p>
                        <p className="truncate text-xs text-zinc-400">{user.email}</p>
                      </div>
                    </div>
                    <div className="py-1.5 text-sm">
                      <MenuLink to="/ratings" icon={<Star className="h-4 w-4 text-amber-400" />}>
                        My Ratings
                      </MenuLink>
                      <MenuLink to="/recommendations" icon={<Sparkles className="h-4 w-4 text-[#e50914]" />}>
                        AI Recommendations
                      </MenuLink>
                      <button
                        role="menuitem"
                        onClick={() => {
                          setMenuOpen(false);
                          logout();
                          navigate('/login');
                        }}
                        className="flex w-full items-center gap-3 border-t border-white/10 px-4 py-2.5 text-zinc-300 transition-colors hover:bg-white/5 hover:text-white"
                      >
                        <LogOut className="h-4 w-4" /> Sign out
                      </button>
                    </div>
                  </div>
                )}
              </div>
            </>
          ) : (
            <Link
              to="/login"
              className="rounded-md bg-[#e50914] px-4 py-1.5 text-sm font-bold text-white transition-all hover:bg-[#f6121d] active:scale-95"
            >
              Sign In
            </Link>
          )}

          <button
            onClick={() => setMobileOpen((o) => !o)}
            className="p-2 text-white md:hidden"
            aria-label="Menu"
            aria-expanded={mobileOpen}
          >
            {mobileOpen ? <X className="h-6 w-6" /> : <Menu className="h-6 w-6" />}
          </button>
        </div>
      </nav>

      {/* Mobile drawer */}
      <div
        className={`grid overflow-hidden transition-all duration-500 ease-out md:hidden ${
          mobileOpen ? 'grid-rows-[1fr] opacity-100' : 'grid-rows-[0fr] opacity-0'
        }`}
      >
        <div className="min-h-0">
          <form onSubmit={submitSearch} className="px-4 pb-2 pt-1">
            <div className="flex items-center gap-2 rounded-md bg-white/10 px-3">
              <Search className="h-4 w-4 text-zinc-400" />
              <input
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                placeholder="Search titles…"
                className="h-10 w-full bg-transparent text-sm text-white placeholder-zinc-500 outline-none"
              />
            </div>
          </form>
          <ul className="px-2 pb-4">
            {NAV_LINKS.map((link) => (
              <li key={link.path}>
                <NavLink
                  to={link.path}
                  end={link.path === '/'}
                  className={({ isActive }) =>
                    `block rounded-md px-3 py-3 text-base transition-colors ${
                      isActive ? 'bg-white/10 font-bold text-white' : 'text-zinc-300 hover:bg-white/5'
                    }`
                  }
                >
                  {link.name}
                </NavLink>
              </li>
            ))}
          </ul>
        </div>
      </div>
    </header>
  );
};

const MenuLink: React.FC<{ to: string; icon: React.ReactNode; children: React.ReactNode }> = ({
  to,
  icon,
  children,
}) => (
  <Link
    to={to}
    role="menuitem"
    className="flex items-center gap-3 px-4 py-2.5 text-zinc-300 transition-colors hover:bg-white/5 hover:text-white"
  >
    {icon}
    {children}
  </Link>
);
