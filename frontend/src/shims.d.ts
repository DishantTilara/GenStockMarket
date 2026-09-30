/* Ambient TypeScript Declarations for React, React-DOM, Router, Vite, and Lucide */

declare namespace JSX {
  interface IntrinsicElements {
    [elemName: string]: any;
  }
}

declare namespace React {
  export type ReactNode = any;
  export type FC<P = {}> = (props: P) => any;
  export type ComponentType<P = {}> = (props: P) => any;
  export type FormEvent<T = any> = any;
  export type ChangeEvent<T = any> = any;
  export type MouseEvent<T = any> = any;
  export type Dispatch<A> = (value: A) => void;
  export type SetStateAction<S> = S | ((prevState: S) => S);
}

declare module 'react' {
  export type ReactNode = any;
  export type FC<P = {}> = (props: P) => any;
  export type ComponentType<P = {}> = (props: P) => any;
  export type FormEvent<T = any> = any;
  export type ChangeEvent<T = any> = any;
  export type MouseEvent<T = any> = any;
  export type Dispatch<A> = (value: A) => void;
  export type SetStateAction<S> = S | ((prevState: S) => S);

  export interface Context<T> {
    Provider: any;
    Consumer: any;
    displayName?: string;
  }

  export function useState<T>(initialState: T | (() => T)): [T, (value: T | ((prev: T) => T)) => void];
  export function useEffect(effect: () => void | (() => void), deps?: readonly any[]): void;
  export function useCallback<T extends (...args: any[]) => any>(callback: T, deps: readonly any[]): T;
  export function useMemo<T>(factory: () => T, deps: readonly any[] | undefined): T;
  export function useRef<T>(initialValue?: T): { current: T };
  export function createContext<T>(defaultValue: T): Context<T>;
  export function useContext<T>(context: Context<T>): T;
  
  const React: any;
  export default React;
}

declare module 'react/jsx-runtime' {
  export const jsx: any;
  export const jsxs: any;
  export const Fragment: any;
}

declare module 'react/jsx-dev-runtime' {
  export const jsxDEV: any;
  export const Fragment: any;
}

declare module 'react-router-dom' {
  export const BrowserRouter: any;
  export const Routes: any;
  export const Route: any;
  export const Link: any;
  export const NavLink: any;
  export const Navigate: any;
  export function useNavigate(): (to: string | number, options?: any) => void;
  export function useParams<T = Record<string, string>>(): T;
  export function useLocation(): { pathname: string; search: string; hash: string; state: any; key: string };
}

declare module 'vite' {
  export function defineConfig(config: any): any;
  export interface UserConfig {
    [key: string]: any;
  }
}

declare module '@vitejs/plugin-react' {
  export default function react(options?: any): any;
}

declare module 'lucide-react' {
  export const TrendingUp: any;
  export const TrendingDown: any;
  export const Wallet: any;
  export const LineChart: any;
  export const Brain: any;
  export const AlertTriangle: any;
  export const ShieldCheck: any;
  export const Activity: any;
  export const RefreshCw: any;
  export const Search: any;
  export const Newspaper: any;
  export const ArrowUpRight: any;
  export const ArrowDownRight: any;
  export const Clock: any;
  export const CheckCircle2: any;
  export const XCircle: any;
  export const AlertCircle: any;
  export const Play: any;
  export const Sliders: any;
  export const Send: any;
  export const Bot: any;
  export const User: any;
  export const DollarSign: any;
  export const ArrowDownLeft: any;
  export const Shield: any;
  export const Settings: any;
  export const LogOut: any;
  export const LogIn: any;
  export const UserPlus: any;
  export const Bell: any;
  export const Plus: any;
  export const Trash2: any;
  export const Eye: any;
  export const Sparkles: any;
  export const BarChart3: any;
  export const HelpCircle: any;
  export const Lock: any;
  export const Check: any;
  export const X: any;
  export const ArrowRight: any;
  export const Terminal: any;
  export const Zap: any;
  export const BarChart2: any;
  export const Layers: any;
  export const Compass: any;
  export const ExternalLink: any;
  export const Filter: any;
  export const Bookmark: any;
  export const BookmarkCheck: any;

  const icons: Record<string, any>;
  export default icons;
}
