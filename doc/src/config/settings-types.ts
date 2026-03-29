export interface HeaderNavItem {
  label: string;
  labelKey?: string;
  path: string;
  categoryMatch?: string;
}

export interface ColorModeConfig {
  defaultMode: "light" | "dark";
  lightScheme: string;
  darkScheme: string;
  respectPrefersColorScheme: boolean;
}

export interface FooterLinkItem {
  label: string;
  href: string;
}

export interface FooterLinkColumn {
  title: string;
  items: FooterLinkItem[];
}

export interface FooterConfig {
  links: FooterLinkColumn[];
  /** Copyright text displayed at the bottom of the footer. HTML is supported. */
  copyright?: string;
}
