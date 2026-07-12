import '../styles/globals.css';
import { AuthProvider } from '../context/AuthContext';
import { AnimatePresence, motion } from 'framer-motion';
import { useRouter } from 'next/router';
import ProductionVersionBadge from '../components/ProductionVersionBadge';

function MyApp({ Component, pageProps }) {
  const router = useRouter();

  return (
    <AuthProvider>
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
    </AuthProvider>
  );
}

export default MyApp;   
