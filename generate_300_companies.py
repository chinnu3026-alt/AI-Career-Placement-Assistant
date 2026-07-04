import json
import sqlite3
import random
import os

cities_list = [
    "Bangalore", "Hyderabad", "Chennai", "Pune", "Mysore", "Delhi", "Mumbai", "Noida", "Gurgaon", "Kochi"
]

# High-fidelity realistic profiles for top companies
REAL_COMPANIES_DATA = {
    "Google": {
        "domain": "google.com",
        "hq": "Mountain View, California, USA",
        "bangalore_office": "Bagmane Constellation Business Park, Outer Ring Rd, Doddanekundi, Bengaluru, Karnataka 560037",
        "website": "https://www.google.com",
        "careers_page": "https://careers.google.com",
        "employee_count": "150,000+",
        "founded_year": 1998,
        "description": "Google is a global technology leader focusing on search engine technology, cloud computing, computer software, quantum computing, and artificial intelligence.",
        "hiring_process": "Online Coding Challenge -> 3 rounds of Technical Interviews (focusing on DSA & System Design) -> Googlyness & Leadership Interview",
        "min_cgpa": 8.0,
        "package_range": "18-45 LPA"
    },
    "Microsoft": {
        "domain": "microsoft.com",
        "hq": "Redmond, Washington, USA",
        "bangalore_office": "Vigyan, Prestige Ferns Ridge, Outer Ring Rd, Bellandur, Bengaluru, Karnataka 560103",
        "website": "https://www.microsoft.com",
        "careers_page": "https://careers.microsoft.com",
        "employee_count": "220,000+",
        "founded_year": 1975,
        "description": "Microsoft is a worldwide provider of software, services, devices, and solutions, famous for OS Windows, Office Suite, and Azure cloud solutions.",
        "hiring_process": "Online Coding Assessment -> 2-3 Technical Rounds -> Hiring Manager & Culture Fit Review",
        "min_cgpa": 8.0,
        "package_range": "16-44 LPA"
    },
    "Amazon": {
        "domain": "amazon.com",
        "hq": "Seattle, Washington, USA",
        "bangalore_office": "Bagmane World Technology Center, Mahadevapura, Bengaluru, Karnataka 560048",
        "website": "https://www.amazon.in",
        "careers_page": "https://www.amazon.jobs",
        "employee_count": "1,500,000+",
        "founded_year": 1994,
        "description": "Amazon is a multinational technology giant focusing on e-commerce, cloud computing (AWS), digital streaming, and artificial intelligence.",
        "hiring_process": "Online Test (Coding + Work Simulation) -> 3 Technical SDE Rounds -> Bar Raiser Leadership Principles Interview",
        "min_cgpa": 7.5,
        "package_range": "15-42 LPA"
    },
    "Adobe": {
        "domain": "adobe.com",
        "hq": "San Jose, California, USA",
        "bangalore_office": "Prestige Platina, Outer Ring Road, Marathahalli, Bengaluru, Karnataka 560103",
        "website": "https://www.adobe.com",
        "careers_page": "https://careers.adobe.com",
        "employee_count": "26,000+",
        "founded_year": 1982,
        "description": "Adobe is an industry leader in creative software products, digital media, and marketing solutions, famous for Photoshop, Illustrator, and PDF format.",
        "hiring_process": "Online Coding Round -> 2 Technical Rounds (DSA, OOP, System Design) -> HR Manager Round",
        "min_cgpa": 8.0,
        "package_range": "16-40 LPA"
    },
    "Cisco": {
        "domain": "cisco.com",
        "hq": "San Jose, California, USA",
        "bangalore_office": "Cisco Cessna Business Park, Kadubeesanahalli, Bengaluru, Karnataka 560103",
        "website": "https://www.cisco.com",
        "careers_page": "https://jobs.cisco.com",
        "employee_count": "80,000+",
        "founded_year": 1984,
        "description": "Cisco Systems is a technology conglomerate developing, manufacturing, and selling networking hardware, software, telecommunications equipment, and cybersecurity services.",
        "hiring_process": "Aptitude & Technical MCQ Test -> Technical SDE Round -> Managerial Round -> HR Interview",
        "min_cgpa": 7.5,
        "package_range": "14-30 LPA"
    },
    "NVIDIA": {
        "domain": "nvidia.com",
        "hq": "Santa Clara, California, USA",
        "bangalore_office": "Bagmane Tech Park, Byrasandra, Bengaluru, Karnataka 560093",
        "website": "https://www.nvidia.com",
        "careers_page": "https://www.nvidia.com/en-us/about-nvidia/careers",
        "employee_count": "26,000+",
        "founded_year": 1993,
        "description": "NVIDIA is a pioneer in GPU-accelerated computing, designing graphics processing units for gaming, professional visualization, and AI supercomputing chips.",
        "hiring_process": "Technical Screening -> 3 Core Technical Coding & Hardware Architecture Rounds -> HR Review",
        "min_cgpa": 8.0,
        "package_range": "18-48 LPA"
    },
    "Intel": {
        "domain": "intel.com",
        "hq": "Santa Clara, California, USA",
        "bangalore_office": "Intel India, Outer Ring Rd, Devarabisanahalli, Bengaluru, Karnataka 560103",
        "website": "https://www.intel.com",
        "careers_page": "https://jobs.intel.com",
        "employee_count": "120,000+",
        "founded_year": 1968,
        "description": "Intel is one of the world's largest semiconductor chip manufacturers and developers of advanced processor architectures for servers, computers, and embedded devices.",
        "hiring_process": "Technical MCQs & Coding Assessment -> 2 Rounds of Technical Interviews -> HR Round",
        "min_cgpa": 7.5,
        "package_range": "14-32 LPA"
    },
    "Oracle": {
        "domain": "oracle.com",
        "hq": "Austin, Texas, USA",
        "bangalore_office": "Oracle Technology Park, Bannerghatta Main Rd, Bengaluru, Karnataka 560029",
        "website": "https://www.oracle.com",
        "careers_page": "https://careers.oracle.com",
        "employee_count": "143,000+",
        "founded_year": 1977,
        "description": "Oracle is a multinational computer technology corporation selling database software, cloud systems, and enterprise software products.",
        "hiring_process": "Aptitude, Core CS & Coding Test -> 2 Technical Rounds -> HR Interview",
        "min_cgpa": 7.5,
        "package_range": "13-32 LPA"
    },
    "Salesforce": {
        "domain": "salesforce.com",
        "hq": "San Francisco, California, USA",
        "bangalore_office": "Bagmane Solarium City, Doddanekundi, Bengaluru, Karnataka 560048",
        "website": "https://www.salesforce.com",
        "careers_page": "https://www.salesforce.com/company/careers",
        "employee_count": "79,000+",
        "founded_year": 1999,
        "description": "Salesforce is the global leader in customer relationship management (CRM) software, cloud databases, and customer success solutions.",
        "hiring_process": "Online Coding Round -> 2 Technical SDE Rounds -> Managerial/System Design Interview -> Culture Fit Round",
        "min_cgpa": 8.0,
        "package_range": "15-40 LPA"
    },
    "SAP": {
        "domain": "sap.com",
        "hq": "Walldorf, Germany",
        "bangalore_office": "SAP Labs India, 138, EPIP Zone, Whitefield, Bengaluru, Karnataka 560066",
        "website": "https://www.sap.com",
        "careers_page": "https://jobs.sap.com",
        "employee_count": "111,000+",
        "founded_year": 1972,
        "description": "SAP is the world's leading enterprise resource planning (ERP) software provider, serving companies with business operations management.",
        "hiring_process": "Coding Test -> 2 Technical Interview Rounds -> Managerial Round -> HR Interview",
        "min_cgpa": 7.5,
        "package_range": "12-32 LPA"
    },
    "Dell": {
        "domain": "dell.com",
        "hq": "Round Rock, Texas, USA",
        "bangalore_office": "Dell Technologies, Divyasree Greens, Inner Ring Rd, Bengaluru, Karnataka 560071",
        "website": "https://www.dell.com",
        "careers_page": "https://jobs.dell.com",
        "employee_count": "133,000+",
        "founded_year": 1984,
        "description": "Dell Technologies is a multinational technology giant developing, selling, repairing, and supporting personal computers, servers, data storage devices, and networking solutions.",
        "hiring_process": "Online Aptitude & Coding Test -> Technical Interview -> Managerial Round -> HR Round",
        "min_cgpa": 7.0,
        "package_range": "10-25 LPA"
    },
    "HP": {
        "domain": "hp.com",
        "hq": "Palo Alto, California, USA",
        "bangalore_office": "HP India, 24, Salarpuria Arena, Hosur Rd, Bengaluru, Karnataka 560030",
        "website": "https://www.hp.com",
        "careers_page": "https://jobs.hp.com",
        "employee_count": "58,000+",
        "founded_year": 1939,
        "description": "HP is a computer hardware developer specializing in personal computers, high-volume printers, and 3D printing technologies.",
        "hiring_process": "Online Test -> Technical SDE Round -> Hiring Manager Round -> HR Interview",
        "min_cgpa": 7.0,
        "package_range": "9-22 LPA"
    },
    "IBM": {
        "domain": "ibm.com",
        "hq": "Armonk, New York, USA",
        "bangalore_office": "IBM India, Embassy GolfLinks Business Park, Outer Ring Rd, Bengaluru, Karnataka 560071",
        "website": "https://www.ibm.com",
        "careers_page": "https://www.ibm.com/employment",
        "employee_count": "288,000+",
        "founded_year": 1911,
        "description": "IBM is a leading technology corporation specializing in business hosting, cloud computing infrastructure, mainframe hardware, consulting services, and quantum research.",
        "hiring_process": "Cognitive & Aptitude Test -> Technical Coding Assessment -> Technical Round -> HR Round",
        "min_cgpa": 7.0,
        "package_range": "8-25 LPA"
    },
    "Accenture": {
        "domain": "accenture.com",
        "hq": "Dublin, Ireland",
        "bangalore_office": "Accenture Services, IBC Knowledge Park, Bannerghatta Rd, Bengaluru, Karnataka 560029",
        "website": "https://www.accenture.com",
        "careers_page": "https://www.accenture.com/in-en/careers",
        "employee_count": "733,000+",
        "founded_year": 1989,
        "description": "Accenture is a global professional services firm specializing in digital transformations, IT consulting, application outsourcing, and cloud infrastructure.",
        "hiring_process": "Cognitive & Technical Assessment -> Coding Test -> Technical Interview -> HR Round",
        "min_cgpa": 6.5,
        "package_range": "4.5-12 LPA"
    },
    "Infosys": {
        "domain": "infosys.com",
        "hq": "Bangalore, Karnataka, India",
        "bangalore_office": "Infosys Limited, Electronics City, Hosur Rd, Bengaluru, Karnataka 560100",
        "website": "https://www.infosys.com",
        "careers_page": "https://www.infosys.com/careers.html",
        "employee_count": "335,000+",
        "founded_year": 1981,
        "description": "Infosys is a multinational information technology services corporation providing software development, maintenance, business consulting, and system integration services.",
        "hiring_process": "Infosys Aptitude & Coding Exam -> Technical Interview -> HR Interview",
        "min_cgpa": 6.0,
        "package_range": "3.6-9 LPA"
    },
    "TCS": {
        "domain": "tcs.com",
        "hq": "Mumbai, Maharashtra, India",
        "bangalore_office": "TCS, Think Campus, Electronics City, Bengaluru, Karnataka 560100",
        "website": "https://www.tcs.com",
        "careers_page": "https://www.tcs.com/careers",
        "employee_count": "614,000+",
        "founded_year": 1968,
        "description": "Tata Consultancy Services is the largest IT consulting and software services exporter in India, offering digital systems engineering and business services.",
        "hiring_process": "TCS NQT (National Qualifier Test) -> Technical Interview -> HR Interview",
        "min_cgpa": 6.0,
        "package_range": "3.6-7.2 LPA"
    },
    "Wipro": {
        "domain": "wipro.com",
        "hq": "Bangalore, Karnataka, India",
        "bangalore_office": "Wipro Limited, Doddakannelli, Sarjapur Road, Bengaluru, Karnataka 560035",
        "website": "https://www.wipro.com",
        "careers_page": "https://careers.wipro.com",
        "employee_count": "245,000+",
        "founded_year": 1945,
        "description": "Wipro is a prominent global information technology consulting and business process outsourcing provider, driving enterprise digitization projects.",
        "hiring_process": "Online Aptitude & Coding Test -> Technical Interview -> HR Interview",
        "min_cgpa": 6.0,
        "package_range": "3.5-8 LPA"
    },
    "Cognizant": {
        "domain": "cognizant.com",
        "hq": "Teaneck, New Jersey, USA",
        "bangalore_office": "Cognizant Solutions, Manyata Embassy Business Park, Outer Ring Rd, Bengaluru, Karnataka 560045",
        "website": "https://www.cognizant.com",
        "careers_page": "https://careers.cognizant.com",
        "employee_count": "347,000+",
        "founded_year": 1994,
        "description": "Cognizant is a leading provider of digital, operations, technology consulting, and custom business application services worldwide.",
        "hiring_process": "Online Coding & Aptitude Assessment -> Technical Interview -> HR Interview",
        "min_cgpa": 6.0,
        "package_range": "4-9 LPA"
    },
    "Capgemini": {
        "domain": "capgemini.com",
        "hq": "Paris, France",
        "bangalore_office": "Capgemini India, 158-C, Electronics City, Phase 1, Bengaluru, Karnataka 560100",
        "website": "https://www.capgemini.com",
        "careers_page": "https://www.capgemini.com/careers",
        "employee_count": "340,000+",
        "founded_year": 1967,
        "description": "Capgemini is a multinational information technology services consulting company partnering with enterprises to streamline systems development and IT strategy.",
        "hiring_process": "Written Aptitude & Pseudo-coding test -> Technical SDE Round -> HR Interview",
        "min_cgpa": 6.0,
        "package_range": "3.8-8 LPA"
    },
    "Deloitte": {
        "domain": "deloitte.com",
        "hq": "London, United Kingdom",
        "bangalore_office": "Deloitte Office, Divyasree Royal Harbor, Yemlur, Bengaluru, Karnataka 560037",
        "website": "https://www.deloitte.com",
        "careers_page": "https://jobs2.deloitte.com",
        "employee_count": "450,000+",
        "founded_year": 1845,
        "description": "Deloitte is a global 'Big Four' consulting firm delivering management, risk advisory, enterprise systems integration, and cybersecurity services.",
        "hiring_process": "Online Cognitive & Technical MCQs -> Group Discussion -> Technical Interview -> HR Round",
        "min_cgpa": 6.5,
        "package_range": "5-11 LPA"
    },
    "Flipkart": {
        "domain": "flipkart.com",
        "hq": "Bangalore, Karnataka, India",
        "bangalore_office": "Flipkart Tech Campus, Cessna Business Park, Outer Ring Rd, Bellandur, Bengaluru, Karnataka 560103",
        "website": "https://www.flipkart.com",
        "careers_page": "https://www.flipkartcareers.com",
        "employee_count": "35,000+",
        "founded_year": 2007,
        "description": "Flipkart is India's leading digital e-commerce marketplace, operating under Walmart ownership and providing large-scale systems engineering roles.",
        "hiring_process": "Online Machine Coding Round -> 2 SDE Technical Interviews -> Hiring Manager Round",
        "min_cgpa": 7.0,
        "package_range": "16-32 LPA"
    },
    "Swiggy": {
        "domain": "swiggy.com",
        "hq": "Bangalore, Karnataka, India",
        "bangalore_office": "Swiggy Headquarters, Embassy TechVillage, Devarabisanahalli, Bengaluru, Karnataka 560103",
        "website": "https://www.swiggy.com",
        "careers_page": "https://careers.swiggy.com",
        "employee_count": "10,000+",
        "founded_year": 2014,
        "description": "Swiggy is India's leading on-demand convenience platform, offering food delivery, instant grocery delivery (Instamart), and logistics systems.",
        "hiring_process": "Online Coding Test -> Machine Coding Round -> 2 Technical Interviews -> HR Round",
        "min_cgpa": 7.0,
        "package_range": "14-28 LPA"
    },
    "Zomato": {
        "domain": "zomato.com",
        "hq": "Gurgaon, Haryana, India",
        "bangalore_office": "Zomato office, 3rd Floor, Prestige Star, Intermediate Ring Rd, Domlur, Bengaluru, Karnataka 560071",
        "website": "https://www.zomato.com",
        "careers_page": "https://www.zomato.com/careers",
        "employee_count": "5,000+",
        "founded_year": 2008,
        "description": "Zomato is an Indian restaurant aggregator and food delivery company, specializing in real-time order processing, recommendations, and search APIs.",
        "hiring_process": "Coding Assessment -> Machine Coding -> 2 SDE Rounds -> HR & Culture Round",
        "min_cgpa": 7.0,
        "package_range": "15-28 LPA"
    },
    "Paytm": {
        "domain": "paytm.com",
        "hq": "Noida, Uttar Pradesh, India",
        "bangalore_office": "Paytm office, Embassy Star, Palace Rd, Vasanth Nagar, Bengaluru, Karnataka 560001",
        "website": "https://www.paytm.com",
        "careers_page": "https://careers.paytm.com",
        "employee_count": "10,000+",
        "founded_year": 2010,
        "description": "Paytm is an Indian financial services company offering mobile payments, merchant payment APIs, and consumer banking solutions.",
        "hiring_process": "Online Coding Test -> 2-3 Technical Rounds -> HR Round",
        "min_cgpa": 7.0,
        "package_range": "12-25 LPA"
    },
    "PhonePe": {
        "domain": "phonepe.com",
        "hq": "Bangalore, Karnataka, India",
        "bangalore_office": "PhonePe office, Wing A, Ground Floor, Pine Valley, Embassy GolfLinks, Bengaluru, Karnataka 560071",
        "website": "https://www.phonepe.com",
        "careers_page": "https://www.phonepe.com/careers",
        "employee_count": "12,000+",
        "founded_year": 2015,
        "description": "PhonePe is a digital payments and financial services company, operating India's largest UPI transactional payment gateway network.",
        "hiring_process": "Online Coding Assessment -> Machine Coding Round -> 2 Technical Interviews -> HR Round",
        "min_cgpa": 7.5,
        "package_range": "16-32 LPA"
    },
    "Razorpay": {
        "domain": "razorpay.com",
        "hq": "Bangalore, Karnataka, India",
        "bangalore_office": "Razorpay office, SJR Cyber, Laskar Hosur Road, Adugodi, Bengaluru, Karnataka 560030",
        "website": "https://www.razorpay.com",
        "careers_page": "https://razorpay.com/jobs",
        "employee_count": "3,000+",
        "founded_year": 2014,
        "description": "Razorpay is a major FinTech company providing developer-focused payment gateway API integrations and business banking products.",
        "hiring_process": "Online Coding Round -> Machine Coding (API design) -> 2 Technical Rounds -> HR Interview",
        "min_cgpa": 7.0,
        "package_range": "14-28 LPA"
    },
    "OpenAI": {
        "domain": "openai.com",
        "hq": "San Francisco, California, USA",
        "bangalore_office": "Prestige Trade Tower, Palace Rd, High Grounds, Bengaluru, Karnataka 560001",
        "website": "https://www.openai.com",
        "careers_page": "https://openai.com/careers",
        "employee_count": "1,000+",
        "founded_year": 2015,
        "description": "OpenAI is an AI research and deployment company famous for creating large language models such as GPT-4, DALL-E, and ChatGPT.",
        "hiring_process": "Resume Screening -> General Screen -> Technical System Coding -> ML Infrastructure Round -> Onsite Board Interview",
        "min_cgpa": 8.5,
        "package_range": "25-60 LPA"
    },
    "Palo Alto Networks": {
        "domain": "paloaltonetworks.com",
        "hq": "Santa Clara, California, USA",
        "bangalore_office": "Palo Alto office, Prestige Solitaire, Brunton Rd, Craig Park Layout, Bengaluru, Karnataka 560025",
        "website": "https://www.paloaltonetworks.com",
        "careers_page": "https://jobs.paloaltonetworks.com",
        "employee_count": "13,000+",
        "founded_year": 2005,
        "description": "Palo Alto Networks is a global cybersecurity leader designing next-generation firewalls and cloud security software solutions.",
        "hiring_process": "Technical MCQs & Scripting Test -> 2 Security/Network Coding Rounds -> Hiring Manager Interview",
        "min_cgpa": 7.5,
        "package_range": "15-30 LPA"
    },
    "Cloudflare": {
        "domain": "cloudflare.com",
        "hq": "San Francisco, California, USA",
        "bangalore_office": "Bagmane World Technology Center, Outer Ring Rd, Mahadevapura, Bengaluru, Karnataka 560048",
        "website": "https://www.cloudflare.com",
        "careers_page": "https://www.cloudflare.com/careers",
        "employee_count": "3,500+",
        "founded_year": 2009,
        "description": "Cloudflare is a web infrastructure and security company providing CDN service, DDoS mitigation, and distributed domain server hosting.",
        "hiring_process": "Online Coding round -> Systems / Networking Technical Interview -> Manager Round -> HR",
        "min_cgpa": 7.5,
        "package_range": "15-30 LPA"
    }
}

# Base categories and templates for bulk seeding
categories_templates = {
    "Product Based": {
        "tech_skills": "DSA, Python, Java, SQL, Git, System Design, Operating Systems, Computer Networks",
        "soft_skills": "Problem Solving, Communication, Leadership, Collaboration",
        "certs": "AWS Developer, Google Cloud Professional, Azure DevOps",
        "projects": "Large Scale Web App, Distributed Cache System, AI Query Engine",
        "roles": "Software Engineer, Site Reliability Engineer, Data Scientist",
        "min_cgpa": 8.0,
        "package_range": (15, 45),
        "companies": [
            "Google", "Microsoft", "Amazon", "Apple", "Meta", "Netflix", "Adobe", "Oracle", "SAP", "Salesforce",
            "Cisco", "IBM", "Intel", "NVIDIA", "AMD", "Qualcomm", "Atlassian", "Uber", "Twitter", "Zoom",
            "Slack", "Dropbox", "Spotify", "PayPal", "Stripe", "Shopify", "GitHub", "GitLab", "Airbnb", "HubSpot",
            "ServiceNow", "VMware", "Red Hat", "Autodesk", "Palo Alto Networks", "Juniper Networks", "NetApp", "Citrix",
            "Twilio", "Okta", "Cloudflare", "Broadcom", "Sony R&D", "Samsung Labs", "LG Soft", "Panasonic Tech",
            "Toshiba Labs", "Sharp Tech", "Hitachi Solutions", "NEC Technologies", "Fujitsu India", "HP Enterprise", 
            "Dell Technologies", "Lenovo R&D", "Acer Tech", "Asus R&D"
        ]
    },
    "Service Based": {
        "tech_skills": "Java, Python, SQL, HTML, CSS, JavaScript, Git, OOP, Aptitude, Cloud Basics",
        "soft_skills": "Communication Skills, Teamwork, Time Management, Adaptability",
        "certs": "AWS Cloud Practitioner, Azure Fundamentals, Java Associate",
        "projects": "Employee Timesheet Tracker, Local Business Listing Page, Customer Feedback Portal",
        "roles": "Associate Software Engineer, Analyst, Support Engineer",
        "min_cgpa": 6.0,
        "package_range": (3, 8),
        "companies": [
            "Infosys", "TCS", "Wipro", "Accenture", "Capgemini", "Cognizant", "Deloitte", "EY", "KPMG", "PwC",
            "HCL", "Tech Mahindra", "LTIMindtree", "Genpact", "DXC Technology", "NTT Data", "EPAM Systems", "Globant",
            "Endava", "Perficient", "Hexaware", "Virtusa", "Mphasis", "Zensar", "Birlasoft", "Persistent Systems",
            "Sonata Software", "KPIT Technologies", "Tata Elxsi", "L&T Technology Services", "Cyient", "Coforge",
            "UST Global", "Quest Global", "Sogeti", "Expleo"
        ]
    },
    "Startups": {
        "tech_skills": "Node.js, React, Python, JavaScript, MongoDB, Redis, Docker, Git, REST APIs",
        "soft_skills": "Bias for Action, Ownership, Fast Learner, Collaboration",
        "certs": "Docker Certified Associate, AWS Certified Developer",
        "projects": "Real-time Delivery Tracker, Geospatial Location Finder, Chat System Prototype",
        "roles": "Backend SDE, Frontend SDE, Full Stack Engineer",
        "min_cgpa": 7.0,
        "package_range": (10, 25),
        "companies": [
            "Flipkart", "Swiggy", "Zomato", "Meesho", "Ola", "Ather Energy", "Zepto", "Blinkit", "Nykaa", "Unacademy",
            "Byju's", "Upgrad", "Cult.fit", "Dunzo", "Rapido", "ShareChat", "Dailyhunt", "Pocket FM", "Exotel", "LeadSquared",
            "Gupshup", "Whatfix", "Darwinbox", "Yellow.ai", "Licious", "Pharmeasy", "Urban Company", "Spinny", "Cars24",
            "Classplus", "PhysicsWallah", "Doubtnut", "Vedantu", "Eruditus", "Simplilearn", "Scaler", "Porter", "Delhivery",
            "Shadowfax", "Shiprocket", "BlackBuck", "Rivigo", "ElasticRun", "Ninjacart", "WayCool", "DeHaat", "AgroStar",
            "Stellapps", "CropIn", "Ola Electric", "Inmobi", "Glance", "Juspay"
        ]
    },
    "FinTech": {
        "tech_skills": "Python, SQL, Java, Go, Microservices, REST APIs, Cryptography, Postgres, Git",
        "soft_skills": "Analytical Thinking, Problem Solving, High Ownership, Compliance Knowledge",
        "certs": "AWS Certified Developer, Certified Kubernetes Administrator",
        "projects": "Payment Gateway Integration, Ledger Balance System, Fraud Detection Module",
        "roles": "Fintech Engineer, Systems Analyst, Backend Developer",
        "min_cgpa": 7.5,
        "package_range": (12, 35),
        "companies": [
            "PhonePe", "Razorpay", "Paytm", "Zerodha", "Groww", "Cred", "Juspay", "Pine Labs", "BharatPe", "Slice",
            "Jupiter", "Fi Money", "Niyo", "Scripbox", "INDmoney", "Kuvera", "Smallcase", "Wint Wealth", "LiquiLoans",
            "Grip Invest", "KredX", "Lendingkart", "Capital Float", "Indifi", "FlexiLoans", "Rupeek", "KrazyBee",
            "EarlySalary", "Kissht", "Cashe", "mPokket", "ZestMoney", "LazyPay", "Simpl", "postpe", "Uni Cards", "OneCard"
        ]
    },
    "AI Companies": {
        "tech_skills": "Python, Machine Learning, Deep Learning, SQL, PyTorch, TensorFlow, Statistics, NLP, LLMs",
        "soft_skills": "Data Storytelling, Analytical Thinking, Presentation",
        "certs": "TensorFlow Developer, Google Professional Data Engineer, Azure AI Engineer",
        "projects": "Predictive Demand Engine, NLP Sentiment Chatbot, LLM Agent Implementation",
        "roles": "AI Engineer, Machine Learning Developer, Data Architect",
        "min_cgpa": 8.0,
        "package_range": (16, 50),
        "companies": [
            "OpenAI", "Anthropic", "Perplexity", "Cohere", "Scale AI", "Hugging Face", "Midjourney", "Stability AI",
            "Jasper", "Copy.ai", "Writer", "Runway", "Synthesia", "ElevenLabs", "Character.ai", "Adept", "Inflection",
            "Mistral AI", "H2O.ai", "DataRobot", "C3.ai", "Palantir", "Databricks", "Snowflake", "Cloudera", "Talend",
            "Alteryx", "RapidMiner", "Knime", "Dataiku", "Domino Data Lab", "Anaconda", "Weights & Biases", "Commet ML",
            "Neptune.ai", "MLflow", "Kubeflow", "Prefect", "Dagster", "Airflow", "Great Expectations", "dbt Labs",
            "Fivetran", "Stitch Data", "Hevo Data"
        ]
    },
    "Cybersecurity": {
        "tech_skills": "Cyber Security, Networking, TCP/IP, Linux, Python, Cryptography, Pen Testing, Ethical Hacking",
        "soft_skills": "Critical Observation, Technical Writing, Risk Assessment",
        "certs": "Certified Ethical Hacker (CEH), CompTIA Security+, CCNA Security",
        "projects": "Network Packet Analyzer, Encrypted Chat Protocol, Port Scanner script",
        "roles": "Security Analyst, Penetration Tester, Network Security Engineer",
        "min_cgpa": 7.0,
        "package_range": (10, 28),
        "companies": [
            "CrowdStrike", "CyberArk", "Fortinet", "Quick Heal", "K7 Computing", "TAC Security", "Zscaler", 
            "OneTrust", "SailPoint", "Ping Identity", "ForgeRock", "Tenable", "Rapid7", "Qualys", "SentinelOne", 
            "Darktrace", "FireEye", "Trellix", "McAfee", "NortonLifeLock", "Trend Micro", "Sophos", "Kaspersky", 
            "Bitdefender", "ESET", "Malwarebytes", "Avast", "AVG", "F-Secure", "G Data", "BullGuard"
        ]
    }
}

seeded_companies = []
all_companies_names = set()

# Process templates and seed data
for category, details in categories_templates.items():
    companies_list = details["companies"]
    for cname in companies_list:
        if cname in all_companies_names:
            continue
        all_companies_names.add(cname)
        
        # Determine cities (always include Bangalore, sometimes add others)
        cities = ["Bangalore"]
        if random.random() > 0.4:
            cities.append(random.choice(cities_list))
            
        if cname in ["Google", "Microsoft", "Amazon", "Infosys", "TCS", "Wipro", "Accenture", "Capgemini", "Cognizant", "Deloitte", "IBM", "Intel", "NVIDIA", "Oracle", "Salesforce", "SAP", "Dell", "HP"]:
            cities.extend(["Hyderabad", "Pune", "Noida", "Gurgaon"])
            
        cities = list(set(cities))
        
        # Populate detailed realistic attributes
        if cname in REAL_COMPANIES_DATA:
            data = REAL_COMPANIES_DATA[cname]
            domain = data["domain"]
            logo_url = f"https://logo.clearbit.com/{domain}"
            hq = data["hq"]
            blr_office = data["bangalore_office"]
            website = data["website"]
            careers = data["careers_page"]
            employees = data["employee_count"]
            founded = data["founded_year"]
            desc = data["description"]
            hiring = data["hiring_process"]
            pkg_str = data["package_range"]
            min_cgpa = data["min_cgpa"]
        else:
            # Fallback generator
            domain = cname.lower().replace(" ", "").replace("'", "").replace("&", "") + ".com"
            logo_url = f"https://logo.clearbit.com/{domain}"
            
            # Default founded years & employee counts
            if category == "Startups":
                founded = random.randint(2010, 2021)
                employees = f"{random.randint(100, 1500)} Employees"
                hq = f"Bangalore, India"
                blr_office = f"Prestige Tech Park, Outer Ring Rd, Bengaluru"
                industry = "FinTech / Consumer Tech Startup"
            elif category == "AI Companies":
                founded = random.randint(2014, 2022)
                employees = f"{random.randint(50, 1000)} Employees"
                hq = "San Francisco, California, USA"
                blr_office = "WeWork, Outer Ring Road, Bengaluru"
                industry = "Artificial Intelligence & ML Research"
            elif category == "Cybersecurity":
                founded = random.randint(2000, 2015)
                employees = f"{random.randint(1000, 20000)} Employees"
                hq = "San Jose, California, USA"
                blr_office = "Manyata Embassy Business Park, Outer Ring Rd, Bengaluru"
                industry = "Cybersecurity & Data Protection"
            elif category == "Service Based":
                founded = random.randint(1980, 2000)
                employees = "100,000+ Employees"
                hq = "Mumbai, India"
                blr_office = "Electronic City Phase 1, Bengaluru"
                industry = "IT Services & Software Consulting"
            else:
                founded = random.randint(1990, 2010)
                employees = "10,000+ Employees"
                hq = "San Jose, California, USA"
                blr_office = "Cessna Business Park, Bengaluru"
                industry = "Technology & Enterprise Software"
                
            website = f"https://www.{domain}"
            careers = f"https://careers.{domain}"
            desc = f"{cname} is a leading innovator in the {category} sector, specializing in high-scale systems, digital tooling, and next-generation engineering paradigms."
            hiring = "Online Aptitude & Coding assessment -> 2 Technical Interview Rounds -> Managerial & HR Interview"
            
            # Categories package ranges
            min_p, max_p = details["package_range"]
            base_pkg = random.randint(min_p, max_p)
            pkg_str = f"{base_pkg}-{base_pkg + random.randint(3, 8)} LPA"
            min_cgpa = details["min_cgpa"]
            
        seeded_companies.append({
            "name": cname,
            "type": category,
            "branches": "CSE, AI, ECE, ISE" if category == "Service Based" else "CSE, AI, ECE",
            "min_cgpa": min_cgpa,
            "tech_skills": details["tech_skills"],
            "soft_skills": details["soft_skills"],
            "pref_certs": details["certs"],
            "pref_projects": details["projects"],
            "hiring_roles": details["roles"],
            "package_range": pkg_str,
            "cities": cities,
            "logo_url": logo_url,
            "hq": hq,
            "bangalore_office": blr_office,
            "website": website,
            "careers_page": careers,
            "employee_count": employees,
            "industry": category,
            "founded_year": founded,
            "description": desc,
            "hiring_process": hiring
        })

print(f"Total unique companies compiled: {len(seeded_companies)}")

# Save to JSON
seed_path = "/Users/admin/Desktop/AI-Career-Placement-Assistant/companies_seed.json"
with open(seed_path, "w") as f:
    json.dump(seeded_companies, f, indent=4)
print(f"Successfully generated and wrote {len(seeded_companies)} companies to {seed_path}.")

# Connect and write directly to SQLite to ensure database matches
db_path = "/Users/admin/Desktop/AI-Career-Placement-Assistant/database.db"
conn = sqlite3.connect(db_path)
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

# Recreate tables to ensure schema matches
cursor.execute("DROP TABLE IF EXISTS companies")
cursor.execute('''
    CREATE TABLE IF NOT EXISTS companies (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        city TEXT NOT NULL,
        type TEXT NOT NULL,
        branches TEXT NOT NULL,
        min_cgpa REAL NOT NULL,
        tech_skills TEXT NOT NULL,
        soft_skills TEXT NOT NULL,
        pref_certs TEXT NOT NULL,
        pref_projects TEXT NOT NULL,
        hiring_roles TEXT NOT NULL,
        package_range TEXT NOT NULL,
        logo_url TEXT,
        hq TEXT,
        bangalore_office TEXT,
        website TEXT,
        careers_page TEXT,
        employee_count TEXT,
        industry TEXT,
        founded_year INTEGER,
        description TEXT,
        hiring_process TEXT,
        UNIQUE(name, city)
    )
''')

cursor.execute("DELETE FROM company_skills")
conn.commit()

# Seed companies
count_rows = 0
for comp in seeded_companies:
    for city in comp["cities"]:
        cursor.execute('''
            INSERT OR REPLACE INTO companies (
                name, city, type, branches, min_cgpa, tech_skills, soft_skills, 
                pref_certs, pref_projects, hiring_roles, package_range,
                logo_url, hq, bangalore_office, website, careers_page,
                employee_count, industry, founded_year, description, hiring_process
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            comp["name"], city, comp["type"], comp["branches"], comp["min_cgpa"],
            comp["tech_skills"], comp["soft_skills"], comp["pref_certs"], comp["pref_projects"],
            comp["hiring_roles"], comp["package_range"], comp["logo_url"], comp["hq"],
            comp["bangalore_office"], comp["website"], comp["careers_page"],
            comp["employee_count"], comp["industry"], comp["founded_year"],
            comp["description"], comp["hiring_process"]
        ))
        count_rows += 1
        
        # Dynamic populate company_skills
        all_skills = [s.strip() for s in comp["tech_skills"].split(",") if s.strip()] + [s.strip() for s in comp["soft_skills"].split(",") if s.strip()]
        for s in all_skills:
            cursor.execute('''
                INSERT OR IGNORE INTO company_skills (company_name, skill_name) VALUES (?, ?)
            ''', (comp["name"], s))

conn.commit()
conn.close()

print(f"Database successfully reseeded. Injected {count_rows} city rows across {len(seeded_companies)} unique companies.")
