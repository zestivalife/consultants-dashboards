import '../styles/globals.css';
import { AuthProvider } from '../context/AuthContext';
import { TenantProvider } from '../context/TenantContext';
import { AnimatePresence, motion } from 'framer-motion';
import Head from 'next/head';
import { useRouter } from 'next/router';
import ProductionVersionBadge from '../components/ProductionVersionBadge';
import FrontendBuildGate from '../components/FrontendBuildGate';

function MyApp({ Component, pageProps }) {
  const router = useRouter();

  // The marketing root is deliberately isolated from authenticated bootstrap,
  // tenant resolution and the protected-workspace build gate.
  if (router.pathname === '/') {
    return (
      <>
        <Head>
          <link rel="icon" href="/zestiva-logo.png" type="image/png" />
        </Head>
        <Component {...pageProps} />
      </>
    );
  }

  return (
    <FrontendBuildGate>
      <AuthProvider>
        <TenantProvider>
      <Head>
        <link rel="icon" href="/zestiva-logo.png" type="image/png" />
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="anonymous" />
        <link
          href="https://fonts.googleapis.com/css2?family=Poppins:wght@400;500;600;700&display=swap"
          rel="stylesheet"
        />
      </Head>
      <AnimatePresence mode="wait" initial={false}>
        <motion.div
          key={router.asPath}
          initial={{ opacity: 0, y: 8 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, y: -6 }}
          transition={{ duration: 0.2, ease: 'easeOut' }}
        >
          <Component {...pageProps} />
        </motion.div>
      </AnimatePresence>
      <ProductionVersionBadge />
        </TenantProvider>
      </AuthProvider>
    </FrontendBuildGate>
  );
}

export default MyApp;   
