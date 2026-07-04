import os
import re
import sqlite3
import hashlib

db_path = '/Users/admin/Desktop/AI-Career-Placement-Assistant/database.db'
dest_dir = '/Users/admin/Desktop/AI-Career-Placement-Assistant/static/images/companies'
os.makedirs(dest_dir, exist_ok=True)

# 44 Hand-designed custom SVG brand logos
custom_svgs = {
    'google': '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="100%" height="100%">
  <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/>
  <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/>
  <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.06H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.94l2.85-2.22c-.22-.66-.35-1.36-.35-2.09z"/>
  <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.06l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/>
</svg>''',

    'microsoft': '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 23 23" width="100%" height="100%">
  <rect x="0" y="0" width="11" height="11" fill="#F25022"/>
  <rect x="12" y="0" width="11" height="11" fill="#7FBA00"/>
  <rect x="0" y="12" width="11" height="11" fill="#00A4EF"/>
  <rect x="12" y="12" width="11" height="11" fill="#FFB900"/>
</svg>''',

    'amazon': '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 45" width="100%" height="100%">
  <text x="50" y="22" font-family="'Outfit', sans-serif" font-weight="900" font-size="22" fill="#000000" text-anchor="middle">amazon</text>
  <path d="M 22 28 Q 50 38 78 28" fill="none" stroke="#FF9900" stroke-width="3" stroke-linecap="round"/>
  <path d="M 74 24 L 79 28 L 74 32" fill="none" stroke="#FF9900" stroke-width="3" stroke-linecap="round"/>
</svg>''',

    'ibm': '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 45" width="100%" height="100%">
  <text x="50" y="32" font-family="'Outfit', sans-serif" font-weight="900" font-size="34" fill="#006699" text-anchor="middle" letter-spacing="-1.5">IBM</text>
  <rect x="0" y="2" width="100" height="2" fill="#FFFFFF"/>
  <rect x="0" y="6" width="100" height="2" fill="#FFFFFF"/>
  <rect x="0" y="10" width="100" height="2" fill="#FFFFFF"/>
  <rect x="0" y="14" width="100" height="2" fill="#FFFFFF"/>
  <rect x="0" y="18" width="100" height="2" fill="#FFFFFF"/>
  <rect x="0" y="22" width="100" height="2" fill="#FFFFFF"/>
  <rect x="0" y="26" width="100" height="2" fill="#FFFFFF"/>
  <rect x="0" y="30" width="100" height="2" fill="#FFFFFF"/>
  <rect x="0" y="34" width="100" height="2" fill="#FFFFFF"/>
</svg>''',

    'cisco': '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 50" width="100%" height="100%">
  <path d="M 15 32 L 15 22 M 25 32 L 25 12 M 35 32 L 35 17 M 45 32 L 45 2 M 55 32 L 55 2 M 65 32 L 65 17 M 75 32 L 75 12 M 85 32 L 85 22" stroke="#00BCEB" stroke-width="4.5" stroke-linecap="round"/>
  <text x="50" y="46" font-family="'Outfit', sans-serif" font-weight="bold" font-size="12" fill="#006699" text-anchor="middle">CISCO</text>
</svg>''',

    'oracle': '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 120 40" width="100%" height="100%">
  <text x="60" y="28" font-family="'Outfit', sans-serif" font-weight="900" font-size="28" fill="#F30000" text-anchor="middle" letter-spacing="-1">ORACLE</text>
</svg>''',

    'adobe': '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100" width="100%" height="100%">
  <rect width="100" height="100" fill="#FF0000" rx="15"/>
  <path d="M 50 15 L 80 80 L 68 80 L 59 58 L 41 58 L 32 80 L 20 80 Z M 50 35 L 44 48 L 56 48 Z" fill="#FFFFFF"/>
</svg>''',

    'intel': '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 50" width="100%" height="100%">
  <text x="50" y="32" font-family="'Outfit', sans-serif" font-weight="bold" font-size="26" fill="#0071C5" text-anchor="middle" font-style="italic">intel</text>
  <path d="M 12 36 A 40 20 0 0 1 88 18" fill="none" stroke="#0071C5" stroke-width="3" stroke-linecap="round"/>
</svg>''',

    'nvidia': '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100" width="100%" height="100%">
  <rect width="100" height="100" fill="#000000" rx="15"/>
  <path d="M 50 20 C 30 20 15 35 15 55 C 15 75 30 90 50 90 C 70 90 80 75 80 55 M 50 30 C 38 30 25 40 25 55 C 25 70 38 80 50 80 C 62 80 70 70 70 55" fill="none" stroke="#76B900" stroke-width="6" stroke-linecap="round"/>
  <path d="M 50 40 C 44 40 35 47 35 55 C 35 63 44 70 50 70" fill="none" stroke="#76B900" stroke-width="6" stroke-linecap="round"/>
  <polygon points="45,45 55,45 50,30" fill="#76B900"/>
</svg>''',

    'sap': '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 50" width="100%" height="100%">
  <defs>
    <linearGradient id="sapGrad" x1="0%" y1="0%" x2="100%" y2="0%">
      <stop offset="0%" stop-color="#006699"/>
      <stop offset="100%" stop-color="#0080FF"/>
    </linearGradient>
  </defs>
  <path d="M 0 0 L 100 0 L 90 50 L 0 50 Z" fill="url(#sapGrad)"/>
  <text x="45" y="36" font-family="'Outfit', sans-serif" font-weight="900" font-size="28" fill="#FFFFFF" text-anchor="middle">SAP</text>
</svg>''',

    'dell': '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100" width="100%" height="100%">
  <circle cx="50" cy="50" r="42" fill="none" stroke="#007DBA" stroke-width="6"/>
  <text x="50" y="58" font-family="'Outfit', sans-serif" font-weight="bold" font-size="25" fill="#007DBA" text-anchor="middle">DELL</text>
</svg>''',
    'delltechnologies': '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100" width="100%" height="100%">
  <circle cx="50" cy="50" r="42" fill="none" stroke="#007DBA" stroke-width="6"/>
  <text x="50" y="58" font-family="'Outfit', sans-serif" font-weight="bold" font-size="25" fill="#007DBA" text-anchor="middle">DELL</text>
</svg>''',

    'hp': '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100" width="100%" height="100%">
  <circle cx="50" cy="50" r="45" fill="#0096D6"/>
  <text x="47" y="68" font-family="'Outfit', sans-serif" font-weight="bold" font-size="54" fill="#FFFFFF" text-anchor="middle" font-style="italic">hp</text>
</svg>''',
    'hpenterprise': '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100" width="100%" height="100%">
  <circle cx="50" cy="50" r="45" fill="#0096D6"/>
  <text x="47" y="68" font-family="'Outfit', sans-serif" font-weight="bold" font-size="54" fill="#FFFFFF" text-anchor="middle" font-style="italic">hp</text>
</svg>''',

    'salesforce': '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 70" width="100%" height="100%">
  <path d="M 22 45 A 12 12 0 0 1 28 20 A 18 18 0 0 1 68 20 A 14 14 0 0 1 76 45 Z" fill="#00A1E0"/>
  <text x="48" y="40" font-family="'Outfit', sans-serif" font-weight="bold" font-size="10" fill="#FFFFFF" text-anchor="middle">salesforce</text>
</svg>''',

    'servicenow': '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 35" width="100%" height="100%">
  <rect width="100" height="35" rx="5" fill="#293E40"/>
  <text x="15" y="24" font-family="'Outfit', sans-serif" font-weight="bold" font-size="18" fill="#81B900">&lt;</text>
  <text x="55" y="23" font-family="'Outfit', sans-serif" font-weight="bold" font-size="14" fill="#FFFFFF" text-anchor="middle">servicenow</text>
  <text x="90" y="24" font-family="'Outfit', sans-serif" font-weight="bold" font-size="18" fill="#81B900">&gt;</text>
</svg>''',

    'paypal': '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100" width="100%" height="100%">
  <path d="M 30 15 H 60 C 72 15 78 22 75 38 C 71 52 60 58 48 58 H 36 L 28 85 H 12 L 28 15 Z" fill="#003087"/>
  <path d="M 40 28 H 70 C 82 28 88 35 85 51 C 81 65 70 71 58 71 H 46 L 38 98 H 22 L 38 28 Z" fill="#0079C1" opacity="0.9"/>
</svg>''',

    'goldmansachs': '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100" width="100%" height="100%">
  <rect width="100" height="100" fill="#6699CC" rx="15"/>
  <text x="50" y="55" font-family="'Outfit', sans-serif" font-weight="bold" font-size="32" fill="#FFFFFF" text-anchor="middle">GS</text>
</svg>''',

    'jpmorganchase': '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100" width="100%" height="100%">
  <polygon points="50,10 78,22 90,50 78,78 50,90 22,78 10,50 22,22" fill="none" stroke="#1175BA" stroke-width="6"/>
  <text x="50" y="56" font-family="'Outfit', sans-serif" font-weight="bold" font-size="28" fill="#1175BA" text-anchor="middle">JPM</text>
</svg>''',

    'accenture': '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 120 40" width="100%" height="100%">
  <text x="35" y="28" font-family="'Outfit', sans-serif" font-weight="bold" font-size="22" fill="#000000">accenture</text>
  <path d="M 103 14 L 111 20 L 103 26" fill="none" stroke="#A100FF" stroke-width="4.5" stroke-linecap="round" stroke-linejoin="round"/>
</svg>''',

    'deloitte': '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 120 40" width="100%" height="100%">
  <text x="10" y="28" font-family="'Outfit', sans-serif" font-weight="900" font-size="26" fill="#000000">Deloitte</text>
  <circle cx="106" cy="24" r="4.5" fill="#86BC25"/>
</svg>''',

    'capgemini': '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100" width="100%" height="100%">
  <path d="M 50 15 C 65 15 75 25 75 40 C 75 60 50 85 50 85 C 50 85 25 60 25 40 C 25 25 35 15 50 15 Z" fill="#0070AD"/>
  <path d="M 50 35 C 55 35 60 38 60 43 C 60 50 50 65 50 65 C 50 65 40 50 40 43 C 40 38 45 35 50 35 Z" fill="#FFFFFF"/>
</svg>''',

    'infosys': '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 120 40" width="100%" height="100%">
  <text x="60" y="28" font-family="'Outfit', sans-serif" font-weight="bold" font-size="28" fill="#007CC3" text-anchor="middle">Infosys</text>
</svg>''',

    'tcs': '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100" width="100%" height="100%">
  <circle cx="50" cy="50" r="45" fill="#00539C"/>
  <text x="50" y="58" font-family="'Outfit', sans-serif" font-weight="bold" font-size="32" fill="#FFFFFF" text-anchor="middle">TCS</text>
</svg>''',
    'tataconsultancyservices': '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100" width="100%" height="100%">
  <circle cx="50" cy="50" r="45" fill="#00539C"/>
  <text x="50" y="58" font-family="'Outfit', sans-serif" font-weight="bold" font-size="32" fill="#FFFFFF" text-anchor="middle">TCS</text>
</svg>''',

    'wipro': '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100" width="100%" height="100%">
  <circle cx="50" cy="50" r="30" fill="none" stroke="#2B2E83" stroke-width="12"/>
  <circle cx="50" cy="50" r="20" fill="none" stroke="#009639" stroke-width="8"/>
  <circle cx="50" cy="50" r="10" fill="none" stroke="#FFD100" stroke-width="6"/>
  <circle cx="50" cy="50" r="5" fill="#E4002B"/>
</svg>''',

    'hcl': '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 50" width="100%" height="100%">
  <text x="50" y="36" font-family="'Outfit', sans-serif" font-weight="900" font-size="36" fill="#005691" text-anchor="middle" font-style="italic">HCL</text>
</svg>''',

    'cognizant': '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100" width="100%" height="100%">
  <rect width="100" height="100" fill="#003366" rx="15"/>
  <text x="50" y="55" font-family="'Outfit', sans-serif" font-weight="bold" font-size="20" fill="#00BFFF" text-anchor="middle">COGNIZANT</text>
</svg>''',

    'techmahindra': '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 120 50" width="100%" height="100%">
  <text x="60" y="32" font-family="'Outfit', sans-serif" font-weight="900" font-size="16" fill="#E31B23" text-anchor="middle">Tech Mahindra</text>
</svg>''',

    'ey': '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 80 80" width="100%" height="100%">
  <rect width="80" height="80" fill="#2E2E38" rx="15"/>
  <polygon points="50,15 65,30 50,45" fill="#FFE600"/>
  <text x="35" y="48" font-family="'Outfit', sans-serif" font-weight="900" font-size="32" fill="#FFFFFF" text-anchor="middle">EY</text>
</svg>''',

    'kpmg': '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 50" width="100%" height="100%">
  <rect width="100" height="50" fill="#00338D" rx="5"/>
  <text x="50" y="35" font-family="'Outfit', sans-serif" font-weight="900" font-size="28" fill="#FFFFFF" text-anchor="middle">KPMG</text>
</svg>''',

    'pwc': '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100" width="100%" height="100%">
  <rect x="10" y="10" width="40" height="40" fill="#D85604"/>
  <rect x="50" y="10" width="40" height="40" fill="#EB8C00"/>
  <rect x="10" y="50" width="40" height="40" fill="#FFC20E"/>
  <rect x="50" y="50" width="40" height="40" fill="#000000"/>
  <text x="50" y="58" font-family="'Outfit', sans-serif" font-weight="900" font-size="24" fill="#FFFFFF" text-anchor="middle">pwc</text>
</svg>''',

    'flipkart': '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100" width="100%" height="100%">
  <rect width="100" height="100" fill="#2874F0" rx="15"/>
  <path d="M 30 40 L 70 40 L 75 85 L 25 85 Z" fill="#FFE11B"/>
  <path d="M 40 40 A 10 10 0 0 1 60 40" fill="none" stroke="#2874F0" stroke-width="4.5"/>
  <text x="50" y="65" font-family="'Outfit', sans-serif" font-weight="bold" font-size="22" fill="#2874F0" text-anchor="middle">f</text>
</svg>''',

    'phonepe': '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100" width="100%" height="100%">
  <rect width="100" height="100" fill="#5F259F" rx="15"/>
  <text x="50" y="62" font-family="'Outfit', sans-serif" font-weight="900" font-size="44" fill="#FFFFFF" text-anchor="middle">पे</text>
</svg>''',

    'swiggy': '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100" width="100%" height="100%">
  <rect width="100" height="100" fill="#FC8019" rx="15"/>
  <path d="M 50 20 C 35 20 30 35 30 45 C 30 65 50 85 50 85 C 50 85 70 65 70 45 C 70 35 65 20 50 20 Z" fill="#FFFFFF"/>
  <circle cx="50" cy="45" r="10" fill="#FC8019"/>
</svg>''',

    'zomato': '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100" width="100%" height="100%">
  <rect width="100" height="100" fill="#E23744" rx="15"/>
  <path d="M 50 75 C 50 75 25 55 25 38 C 25 25 35 15 50 30 C 65 15 75 25 75 38 C 75 55 50 75 50 75 Z" fill="#FFFFFF"/>
</svg>''',

    'razorpay': '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100" width="100%" height="100%">
  <rect width="100" height="100" fill="#0B49C9" rx="15"/>
  <path d="M 25 35 L 75 35 L 60 70 L 40 70 Z" fill="#00D2FF"/>
  <text x="50" y="56" font-family="'Outfit', sans-serif" font-weight="bold" font-size="12" fill="#FFFFFF" text-anchor="middle">Razorpay</text>
</svg>''',

    'freshworks': '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100" width="100%" height="100%">
  <rect width="100" height="100" fill="#00B660" rx="15"/>
  <path d="M 30 70 Q 50 30 70 70 Z" fill="#FFFFFF"/>
  <circle cx="50" cy="40" r="10" fill="#00B660"/>
</svg>''',

    'zoho': '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100" width="100%" height="100%">
  <rect x="15" y="15" width="30" height="30" fill="#E12128" rx="5"/>
  <rect x="55" y="15" width="30" height="30" fill="#1C86C8" rx="5"/>
  <rect x="15" y="55" width="30" height="30" fill="#F8A71A" rx="5"/>
  <rect x="55" y="55" width="30" height="30" fill="#2E9E47" rx="5"/>
</svg>''',

    # 8 New examples requested:
    'dropbox': '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100" width="100%" height="100%">
  <polygon points="50,15 25,30 50,45 75,30" fill="#0061FE"/>
  <polygon points="50,45 25,60 50,75 75,60" fill="#0061FE"/>
  <polygon points="25,30 0,45 25,60 50,45" fill="#0061FE" opacity="0.85"/>
  <polygon points="75,30 100,45 75,60 50,45" fill="#0061FE" opacity="0.85"/>
  <polygon points="50,75 25,60 0,75 50,95 100,75 75,60" fill="#0061FE" opacity="0.95"/>
</svg>''',

    'elevenlabs': '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100" width="100%" height="100%">
  <rect width="100" height="100" fill="#000000" rx="15"/>
  <rect x="35" y="25" width="10" height="50" fill="#00FFCC" rx="5"/>
  <rect x="55" y="25" width="10" height="50" fill="#00FFCC" rx="5"/>
</svg>''',

    'fivetran': '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100" width="100%" height="100%">
  <rect width="100" height="100" fill="#1C1F2B" rx="15"/>
  <path d="M 25 30 H 75 V 70 H 25 Z" fill="none" stroke="#FF5C35" stroke-width="8" stroke-linecap="round"/>
  <circle cx="50" cy="50" r="12" fill="#00D2FF"/>
</svg>''',

    'fujitsu': '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100" width="100%" height="100%">
  <path d="M 20 50 C 20 30 40 30 50 50 C 60 70 80 70 80 50 C 80 30 60 30 50 50 C 40 70 20 70 20 50 Z" fill="none" stroke="#FF0000" stroke-width="8"/>
  <circle cx="50" cy="30" r="8" fill="#FF0000"/>
</svg>''',
    'fujitsuindia': '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100" width="100%" height="100%">
  <path d="M 20 50 C 20 30 40 30 50 50 C 60 70 80 70 80 50 C 80 30 60 30 50 50 C 40 70 20 70 20 50 Z" fill="none" stroke="#FF0000" stroke-width="8"/>
  <circle cx="50" cy="30" r="8" fill="#FF0000"/>
</svg>''',

    'github': '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100" width="100%" height="100%">
  <rect width="100" height="100" fill="#181717" rx="15"/>
  <path d="M50 12C28.5 12 11 29.5 11 51c0 17.2 11.1 31.8 26.6 37 2 .3 2.7-.8 2.7-1.9v-6.7c-10.8 2.3-13.1-5.2-13.1-5.2-1.8-4.5-4.3-5.7-4.3-5.7-3.5-2.4.3-2.4.3-2.4 3.9.3 6 4 6 4 3.5 6 9.1 4.3 11.3 3.3.3-2.5 1.4-4.3 2.5-5.3-8.6-1-17.7-4.3-17.7-19.3 0-4.3 1.5-7.8 4-10.5-.4-1-.1-4.8.4-10.4 0 0 3.3-1 10.8 4 3.1-.9 6.5-1.3 9.9-1.3s6.8.4 9.9 1.3c7.5-5 10.8-4 10.8-4 .5 5.6.8 9.4.4 10.4 2.5 2.7 4 6.2 4 10.5 0 15-9.1 18.2-17.8 19.2 1.4 1.2 2.7 3.6 2.7 7.2v10.7c0 1.1.7 2.3 2.8 1.9C77.9 82.8 89 68.2 89 51c0-21.5-17.5-39-39-39z" fill="#FFFFFF"/>
</svg>''',

    'gitlab': '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100" width="100%" height="100%">
  <polygon points="50,90 20,40 50,60" fill="#E24329"/>
  <polygon points="50,90 80,40 50,60" fill="#FC6D26"/>
  <polygon points="20,40 5,40 20,10" fill="#FCA326"/>
  <polygon points="80,40 95,40 80,10" fill="#E24329"/>
  <polygon points="20,40 50,60 80,40" fill="#FC6D26"/>
  <polygon points="20,40 20,10 50,60" fill="#FC6D26"/>
  <polygon points="80,40 80,10 50,60" fill="#E24329"/>
</svg>''',

    'h2oai': '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100" width="100%" height="100%">
  <rect width="100" height="100" fill="#FEC524" rx="15"/>
  <path d="M 50 15 C 30 40 30 75 50 85 C 70 75 70 40 50 15 Z" fill="#000000"/>
  <text x="50" y="65" font-family="'Outfit', sans-serif" font-weight="bold" font-size="16" fill="#FFFFFF" text-anchor="middle">H2O</text>
</svg>'''
}

def generate_generic_logo(company_name, val):
    # Deterministic palette of premium gradients
    gradients = [
        ("#4F46E5", "#06B6D4"), # Indigo -> Cyan
        ("#3B82F6", "#8B5CF6"), # Blue -> Purple
        ("#10B981", "#059669"), # Emerald -> Green
        ("#EC4899", "#F43F5E"), # Pink -> Rose
        ("#F59E0B", "#D97706"), # Amber -> Orange
        ("#6366F1", "#A855F7"), # Violet -> Purple
        ("#0ea5e9", "#2563eb"), # Sky -> Blue
        ("#84cc16", "#10b981"), # Lime -> Emerald
        ("#f43f5e", "#b91c1c"), # Rose -> Red
        ("#14b8a6", "#0d9488"), # Teal -> Dark Teal
    ]
    
    grad = gradients[val % len(gradients)]
    c1, c2 = grad
    shape_style = val % 6
    
    # Initials generator
    words = [w for w in re.sub(r'[^a-zA-Z0-9 ]', '', company_name).split() if w]
    if len(words) >= 2:
        initials = "".join(w[0] for w in words[:3]).upper()
    else:
        name_clean = re.sub(r'[^a-zA-Z0-9]', '', company_name)
        if len(name_clean) > 3:
            initials = name_clean[:3].upper()
        else:
            initials = name_clean.upper()
            
    svg_header = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100" width="100%" height="100%">
  <defs>
    <linearGradient id="grad_{val}" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="{c1}" />
      <stop offset="100%" stop-color="{c2}" />
    </linearGradient>
  </defs>
  <!-- Solid Background Plate -->
  <rect width="100" height="100" fill="url(#grad_{val})" rx="24"/>
'''

    # Shape vector generator in subtle transparent white
    if shape_style == 0:
        svg_shape = f'''  <line x1="30" y1="30" x2="70" y2="30" stroke="#FFFFFF" stroke-width="3" opacity="0.25"/>
  <line x1="30" y1="30" x2="50" y2="70" stroke="#FFFFFF" stroke-width="3" opacity="0.25"/>
  <line x1="70" y1="30" x2="50" y2="70" stroke="#FFFFFF" stroke-width="3" opacity="0.25"/>
  <circle cx="30" cy="30" r="6" fill="#FFFFFF" opacity="0.3"/>
  <circle cx="70" cy="30" r="6" fill="#FFFFFF" opacity="0.3"/>
  <circle cx="50" cy="70" r="6" fill="#FFFFFF" opacity="0.3"/>'''
    elif shape_style == 1:
        svg_shape = f'''  <polygon points="50,15 80,32 80,68 50,85 20,68 20,32" fill="none" stroke="#FFFFFF" stroke-width="4" stroke-linejoin="round" opacity="0.25"/>
  <polygon points="50,25 70,37 70,63 50,75 30,63 30,37" fill="#FFFFFF" opacity="0.15"/>'''
    elif shape_style == 2:
        svg_shape = f'''  <circle cx="42" cy="50" r="22" fill="#FFFFFF" opacity="0.2"/>
  <circle cx="58" cy="50" r="22" fill="#FFFFFF" opacity="0.2"/>'''
    elif shape_style == 3:
        svg_shape = f'''  <rect x="25" y="55" width="12" height="20" rx="3" fill="#FFFFFF" opacity="0.25"/>
  <rect x="44" y="35" width="12" height="40" rx="3" fill="#FFFFFF" opacity="0.25"/>
  <rect x="63" y="20" width="12" height="55" rx="3" fill="#FFFFFF" opacity="0.25"/>'''
    elif shape_style == 4:
        svg_shape = f'''  <polygon points="50,20 80,50 50,80 20,50" fill="none" stroke="#FFFFFF" stroke-width="3" opacity="0.25"/>
  <polygon points="50,35 65,50 50,65 35,50" fill="#FFFFFF" opacity="0.2"/>'''
    else:
        svg_shape = f'''  <path d="M 25,50 C 25,35 40,35 50,50 C 60,65 75,65 75,50 C 75,35 60,35 50,50 C 40,65 25,65 25,50 Z" fill="none" stroke="#FFFFFF" stroke-width="5" stroke-linecap="round" opacity="0.25"/>'''

    # High-contrast bold white monogram centered
    svg_text = f'''  <text x="50" y="54" dominant-baseline="middle" text-anchor="middle" font-family="'Outfit', sans-serif" font-size="28" font-weight="900" fill="#FFFFFF">{initials}</text>'''
    
    svg_footer = "\n</svg>"
    return svg_header + svg_shape + svg_text + svg_footer

# Main runner
print("Connecting to database...")
conn = sqlite3.connect(db_path)
conn.row_factory = sqlite3.Row
cursor = conn.cursor()
cursor.execute("SELECT DISTINCT name FROM companies")
rows = cursor.fetchall()
db_companies = [r['name'] for r in rows]
conn.close()

print(f"Total unique companies from DB: {len(db_companies)}")

new_logos_report = []
for name in db_companies:
    # Sanitize key in the exact same format
    key = re.sub(r'[^a-z0-9]', '', name.lower())
    dest_file = os.path.join(dest_dir, f"{key}.svg")
    
    if key in custom_svgs:
        # Save custom SVG
        with open(dest_file, 'w') as f:
            f.write(custom_svgs[key].strip())
        new_logos_report.append((name, "Custom Brand Logo"))
    else:
        # Generate generic SVG
        h = hashlib.md5(name.encode('utf-8')).hexdigest()
        val = int(h, 16)
        content = generate_generic_logo(name, val)
        with open(dest_file, 'w') as f:
            f.write(content.strip())
        new_logos_report.append((name, "Generated Corporate Logo"))

print(f"Successfully wrote {len(new_logos_report)} logo SVG files to {dest_dir}!")

# Verify 100% of database companies have a file
missing = []
for name in db_companies:
    key = re.sub(r'[^a-z0-9]', '', name.lower())
    expected_path = os.path.join(dest_dir, f"{key}.svg")
    if not os.path.exists(expected_path):
        missing.append(name)

if not missing:
    print("VERIFICATION SUCCESS: 100% of companies have a local logo file!")
else:
    print(f"VERIFICATION FAILURE: Missing logos for {len(missing)} companies: {missing}")

# Output generated report overview
print("\n=== GENERATED LOGOS REPORT SUMMARY ===")
custom_count = sum(1 for r in new_logos_report if r[1] == "Custom Brand Logo")
gen_count = sum(1 for r in new_logos_report if r[1] == "Generated Corporate Logo")
print(f"Custom Hand-crafted brand logos: {custom_count}")
print(f"Automatically generated unique corporate logos: {gen_count}")
print(f"Total Logos Written: {len(new_logos_report)}")
