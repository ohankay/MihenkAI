import React from 'react';

interface MihenkLogoProps {
  size?: number;
  className?: string;
}

/**
 * MihenkAI touchstone logo.
 * "Mihenk taşı" — the dark quartz stone used to test the purity of precious metals.
 * The gold streak across the stone face represents the evaluation mark left by tested metal.
 */
const MihenkLogo: React.FC<MihenkLogoProps> = ({ size = 40, className = '' }) => (
  <svg
    width={size}
    height={size}
    viewBox="0 0 48 48"
    fill="none"
    xmlns="http://www.w3.org/2000/svg"
    className={className}
    aria-label="MihenkAI logo"
  >
    {/* Stone body — dark octagon */}
    <polygon
      points="14,4 34,4 44,14 44,34 34,44 14,44 4,34 4,14"
      fill="#1c1917"
      stroke="#57534e"
      strokeWidth="1.5"
    />
    {/* Surface texture — subtle cleavage lines in the stone */}
    <line x1="9" y1="20" x2="20" y2="9" stroke="#44403c" strokeWidth="1.5" />
    <line x1="28" y1="39" x2="39" y2="28" stroke="#44403c" strokeWidth="1.2" />
    {/* Gold test streak — the evaluation mark left by the tested metal */}
    <path
      d="M11 37 C16 30 28 22 37 11"
      stroke="#fbbf24"
      strokeWidth="3.5"
      strokeLinecap="round"
    />
    {/* Glowing tip — where the metal meets the stone */}
    <circle cx="37" cy="11" r="3" fill="#fde68a" />
    <circle cx="37" cy="11" r="1.5" fill="#ffffff" opacity="0.8" />
  </svg>
);

export default MihenkLogo;
