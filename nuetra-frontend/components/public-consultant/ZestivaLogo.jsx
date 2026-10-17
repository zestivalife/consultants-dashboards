import Image from 'next/image';

export default function ZestivaLogo({ className = '' }) {
  return <Image src="/zestiva.svg" alt="Zestiva" width={336} height={86} priority className={className} />;
}
