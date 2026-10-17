import Image from 'next/image';

export default function ZestivaLogo({ className = '' }) {
  return <Image src="/zestiva-logo.png" alt="Zestiva" width={313} height={114} priority className={className} />;
}
