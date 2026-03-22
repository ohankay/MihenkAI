import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import MihenkLogo from './MihenkLogo';

interface NavItem { to: string; label: string; }

const NAV: NavItem[] = [
  { to: '/',           label: 'Dashboard' },
  { to: '/models',     label: 'Judge LLM Profiles' },
  { to: '/profiles',   label: 'Evaluation Profiles' },
  { to: '/api-specs',  label: 'API Specs' },
];

interface AppShellProps {
  children: React.ReactNode;
}

const AppShell: React.FC<AppShellProps> = ({ children }) => {
  const { pathname } = useLocation();

  return (
    <div className="min-h-screen bg-stone-100 flex flex-col">
      {/* ── Top header ───────────────────────────────────────── */}
      <header className="bg-stone-900 shadow-lg flex-shrink-0">
        <div className="max-w-screen-2xl mx-auto px-6 py-4 flex items-center gap-4">
          <Link to="/" className="flex items-center gap-3 no-underline">
            <MihenkLogo size={42} />
            <div>
              <h1 className="text-2xl font-bold text-white tracking-tight leading-none">MihenkAI</h1>
              <p className="text-amber-400 text-xs font-medium mt-0.5">
                DeepEval based Tester Workbench for LLM Applications
              </p>
            </div>
          </Link>
        </div>
      </header>

      <div className="flex flex-1 min-h-0">
        {/* ── Sidebar ──────────────────────────────────────────── */}
        <aside className="w-56 bg-stone-900 border-r border-stone-700 flex-shrink-0">
          <nav className="p-5 space-y-0.5">
            <p className="text-amber-400 text-xs font-semibold uppercase tracking-widest px-3 py-2">
              Navigation
            </p>
            {NAV.map(({ to, label }) => {
              const active = pathname === to || (to !== '/' && pathname.startsWith(to));
              return (
                <Link
                  key={to}
                  to={to}
                  className={`block px-3 py-2.5 rounded-md text-sm font-medium transition-colors ${
                    active
                      ? 'bg-stone-700 text-amber-400'
                      : 'text-stone-300 hover:bg-stone-800 hover:text-amber-300'
                  }`}
                >
                  {label}
                </Link>
              );
            })}
          </nav>
        </aside>

        {/* ── Main content ─────────────────────────────────────── */}
        <main className="flex-1 overflow-y-auto p-8 min-w-0">
          {children}
        </main>
      </div>
    </div>
  );
};

export default AppShell;
