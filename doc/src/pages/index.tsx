import type { ReactNode } from 'react';
import clsx from 'clsx';
import useDocusaurusContext from '@docusaurus/useDocusaurusContext';
import useBaseUrl from '@docusaurus/useBaseUrl';
import Layout from '@theme/Layout';
import DocsSitemap from '@site/src/components/DocsSitemap';
import styles from './index.module.css';

export default function Home(): ReactNode {
  const { siteConfig } = useDocusaurusContext();
  const logoUrl = useBaseUrl('/img/logo.svg');
  return (
    <Layout title={siteConfig.title}>
      <main className={clsx(styles.main)}>
        <div className={styles.twoColLayout}>
          {/* Left Column - Fixed width, scroll-fixed */}
          <aside className={styles.leftCol}>
            <div className={styles.leftColContent}>
              {/* Title and Logo Section */}
              <div className={styles.headerSection}>
                <h1>{siteConfig.title}</h1>
                <p className={styles.tagline}>{siteConfig.tagline}</p>

                {/* Big Logo */}
                <div className={styles.logoContainer}>
                  <img src={logoUrl} alt="USB-PD Synth Power Logo" className={styles.bigLogo} />
                </div>
              </div>

              {/* Quick Links */}
              <section className={styles.linksSection}>
                <h2>Related Links</h2>
                <ul className={styles.linksList}>
                  <li>
                    <a href="https://takazudomodular.com/" rel="noopener noreferrer">
                      Takazudo Modular
                    </a>
                  </li>
                </ul>
              </section>

              {/* Stats Section */}
              <section className={styles.statsSection}>
                <h2>Specifications</h2>
                <div className={styles.statsGrid}>
                  <div className={styles.statItem}>
                    <div className={styles.statNumber}>+12V: 1.2A</div>
                  </div>
                  <div className={styles.statItem}>
                    <div className={styles.statNumber}>-12V: 1A</div>
                  </div>
                  <div className={styles.statItem}>
                    <div className={styles.statNumber}>+5V: 1.2A</div>
                  </div>
                  <div className={styles.statItem}>
                    <div className={styles.statNumber}>USB-PD</div>
                  </div>
                </div>
              </section>
            </div>
          </aside>

          {/* Right Column - Remaining space */}
          <div className={styles.rightCol}>
            {/* Full Documentation Sitemap */}
            <DocsSitemap />
          </div>
        </div>
      </main>
    </Layout>
  );
}
