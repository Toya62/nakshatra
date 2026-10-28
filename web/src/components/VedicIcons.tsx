"use client";

import React from "react";

interface IconProps extends React.SVGProps<SVGSVGElement> {
  size?: number;
}

/** 1. Birth Chart (Kundali Mandala — Classical North Indian 1st Bhava Diamond) */
export const KundaliIcon: React.FC<IconProps> = ({ size = 22, ...props }) => (
  <svg
    viewBox="0 0 24 24"
    width={size}
    height={size}
    fill="none"
    stroke="currentColor"
    strokeWidth="1.85"
    strokeLinecap="round"
    strokeLinejoin="round"
    {...props}
  >
    <rect x="2" y="2" width="20" height="20" rx="1.5" stroke="currentColor" />
    <line x1="2" y1="2" x2="22" y2="22" />
    <line x1="22" y1="2" x2="2" y2="22" />
    <polygon points="12,2 22,12 12,22 2,12" stroke="currentColor" />
    <circle cx="12" cy="12" r="1.5" fill="currentColor" />
  </svg>
);

/** 2. Transits / Gochar (Planetary Orbit Trajectories & Shani Rings) */
export const GocharIcon: React.FC<IconProps> = ({ size = 22, ...props }) => (
  <svg
    viewBox="0 0 24 24"
    width={size}
    height={size}
    fill="none"
    stroke="currentColor"
    strokeWidth="1.85"
    strokeLinecap="round"
    strokeLinejoin="round"
    {...props}
  >
    <circle cx="12" cy="12" r="2.5" fill="currentColor" />
    <ellipse cx="12" cy="12" rx="9" ry="4" transform="rotate(-30 12 12)" stroke="currentColor" strokeDasharray="2 2" />
    <ellipse cx="12" cy="12" rx="10" ry="6" transform="rotate(40 12 12)" stroke="currentColor" />
    <circle cx="19" cy="8" r="2" fill="currentColor" />
    <ellipse cx="19" cy="8" rx="3.5" ry="1.2" transform="rotate(-25 19 8)" stroke="currentColor" strokeWidth="1.4" />
    <circle cx="5" cy="16" r="1.5" fill="currentColor" />
  </svg>
);

/** 3. Vimshottari Dasha (Kalachakra 120-Year Wheel of Time & Gnomon Pointer) */
export const DashaIcon: React.FC<IconProps> = ({ size = 22, ...props }) => (
  <svg
    viewBox="0 0 24 24"
    width={size}
    height={size}
    fill="none"
    stroke="currentColor"
    strokeWidth="1.85"
    strokeLinecap="round"
    strokeLinejoin="round"
    {...props}
  >
    <circle cx="12" cy="12" r="9.5" stroke="currentColor" />
    <circle cx="12" cy="12" r="6.5" stroke="currentColor" strokeDasharray="1.5 2" />
    <circle cx="12" cy="12" r="2.2" fill="currentColor" />
    <line x1="12" y1="2.5" x2="12" y2="5.5" />
    <line x1="12" y1="18.5" x2="12" y2="21.5" />
    <line x1="2.5" y1="12" x2="5.5" y2="12" />
    <line x1="18.5" y1="12" x2="21.5" y2="12" />
    <line x1="12" y1="12" x2="16.5" y2="7.5" strokeWidth="2.2" />
    <circle cx="16.5" cy="7.5" r="1.5" fill="currentColor" />
  </svg>
);

/** 4. Daily Panchanga (Solar-Lunar Tithi Union: Crescent Moon & Morning Sun) */
export const PanchangaIcon: React.FC<IconProps> = ({ size = 22, ...props }) => (
  <svg
    viewBox="0 0 24 24"
    width={size}
    height={size}
    fill="none"
    stroke="currentColor"
    strokeWidth="1.85"
    strokeLinecap="round"
    strokeLinejoin="round"
    {...props}
  >
    <path d="M14.5 3A9 9 0 1 0 21 16.5 7.5 7.5 0 0 1 14.5 3z" stroke="currentColor" fill="none" />
    <circle cx="9.5" cy="13.5" r="3" fill="currentColor" />
    <line x1="9.5" y1="7.5" x2="9.5" y2="9" />
    <line x1="9.5" y1="18" x2="9.5" y2="19.5" />
    <line x1="3.5" y1="13.5" x2="5" y2="13.5" />
    <line x1="14" y1="13.5" x2="15.5" y2="13.5" />
    <line x1="5.2" y1="9.2" x2="6.3" y2="10.3" />
    <line x1="12.7" y1="16.7" x2="13.8" y2="17.8" />
  </svg>
);

/** 5. Kundali Matching (Interlocking Ashtakoota Harmony Mandalas & Auspicious Crest) */
export const MatchingIcon: React.FC<IconProps> = ({ size = 22, ...props }) => (
  <svg
    viewBox="0 0 24 24"
    width={size}
    height={size}
    fill="none"
    stroke="currentColor"
    strokeWidth="1.85"
    strokeLinecap="round"
    strokeLinejoin="round"
    {...props}
  >
    <circle cx="8.5" cy="12.5" r="6" stroke="currentColor" />
    <circle cx="15.5" cy="12.5" r="6" stroke="currentColor" />
    <path d="M12 8 C13.3 9.8 13.3 15.2 12 17 C10.7 15.2 10.7 9.8 12 8 Z" fill="currentColor" opacity="0.3" />
    <polygon points="12,10.5 13,12.5 12,14.5 11,12.5" fill="currentColor" />
    <path d="M7 6L9 8L12 4.5L15 8L17 6" strokeWidth="1.6" />
  </svg>
);

/** 6. Muhurtha & Horas (24-Hora Astronomical Sun Timepiece & Planetary Rays) */
export const MuhurthaIcon: React.FC<IconProps> = ({ size = 22, ...props }) => (
  <svg
    viewBox="0 0 24 24"
    width={size}
    height={size}
    fill="none"
    stroke="currentColor"
    strokeWidth="1.85"
    strokeLinecap="round"
    strokeLinejoin="round"
    {...props}
  >
    <circle cx="12" cy="12" r="9.5" stroke="currentColor" />
    <line x1="12" y1="2.5" x2="12" y2="4.5" />
    <line x1="21.5" y1="12" x2="19.5" y2="12" />
    <line x1="12" y1="21.5" x2="12" y2="19.5" />
    <line x1="2.5" y1="12" x2="4.5" y2="12" />
    <circle cx="12" cy="12" r="3" fill="currentColor" />
    <line x1="12" y1="6" x2="12" y2="18" strokeDasharray="1 3" />
    <line x1="6" y1="12" x2="18" y2="12" strokeDasharray="1 3" />
    <line x1="12" y1="12" x2="15.5" y2="8.5" strokeWidth="2.2" />
  </svg>
);

/** 7. Remedies & Upayas (Ashtadala Lotus & Navaratna Diamond Yantra Shield) */
export const RemediesIcon: React.FC<IconProps> = ({ size = 22, ...props }) => (
  <svg
    viewBox="0 0 24 24"
    width={size}
    height={size}
    fill="none"
    stroke="currentColor"
    strokeWidth="1.85"
    strokeLinecap="round"
    strokeLinejoin="round"
    {...props}
  >
    <path d="M12 3 C10 7 10 10 12 12 C14 10 14 7 12 3 Z" fill="currentColor" opacity="0.25" />
    <path d="M12 21 C10 17 10 14 12 12 C14 14 14 17 12 21 Z" fill="currentColor" opacity="0.25" />
    <path d="M3 12 C7 10 10 10 12 12 C10 14 7 14 3 12 Z" fill="currentColor" opacity="0.25" />
    <path d="M21 12 C17 10 14 10 12 12 C14 14 17 14 21 12 Z" fill="currentColor" opacity="0.25" />
    <polygon points="12,5.5 18.5,12 12,18.5 5.5,12" stroke="currentColor" />
    <circle cx="12" cy="12" r="1.8" fill="currentColor" />
  </svg>
);

/** 8. AI Consultation (Ajna Third-Eye Chakra & Sacred Celestial Oracle Star) */
export const ConsultationIcon: React.FC<IconProps> = ({ size = 22, ...props }) => (
  <svg
    viewBox="0 0 24 24"
    width={size}
    height={size}
    fill="none"
    stroke="currentColor"
    strokeWidth="1.85"
    strokeLinecap="round"
    strokeLinejoin="round"
    {...props}
  >
    <path d="M2 12 C6 5.5 18 5.5 22 12 C18 18.5 6 18.5 2 12 Z" stroke="currentColor" />
    <circle cx="12" cy="12" r="4.5" stroke="currentColor" strokeDasharray="2 1.5" />
    <polygon points="12,8.5 13,11 15.5,12 13,13 12,15.5 11,13 8.5,12 11,11" fill="currentColor" />
  </svg>
);
