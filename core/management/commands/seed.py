"""Populate the site with Right Point Solutions content.

Idempotent: run `python manage.py seed` any time. Pass `--flush` first if you
want a clean rebuild of the catalogue.
"""

import datetime

from django.core.management.base import BaseCommand
from django.db import transaction

from casestudies.models import CaseStudy
from core.models import SiteSetting
from products.models import Brand, Product, ProductCategory
from solutions.models import ProcessStep, Solution, WhyPoint

SOLUTIONS = [
    {
        "slug": "cctv-video-intelligence",
        "title": "CCTV & Video Intelligence",
        "kicker": "See the system",
        "icon": "camera",
        "image_caption": "IP dome camera on a bracket",
        "order": 1,
        "tags": "IP surveillance, Remote monitoring, Analytics",
        "summary": (
            "See more, react faster. We design and deploy high-definition surveillance "
            "systems with intelligent monitoring for homes, campuses, retail and enterprise sites."
        ),
        "intro": (
            "Surveillance should do more than record. We design video systems that help teams "
            "see clearly, verify faster and respond with confidence."
        ),
        "deliverables": "\n".join(
            [
                "IP camera design and deployment",
                "Remote monitoring and control-room workflows",
                "Video analytics, alerts and intelligent search",
                "Structured cabling, storage and system handover",
            ]
        ),
        "outcomes": "\n".join(
            [
                "Coverage you can trust in daylight, low light and at entry points",
                "Recordings that survive the retention period and export cleanly as evidence",
                "Operators who can find the right footage in minutes, not hours",
            ]
        ),
        "meta_description": (
            "IP camera design, remote monitoring, video analytics and structured cabling for "
            "homes, campuses, retail and enterprise sites in Kenya."
        ),
        "steps": [
            ("Assess", "Understand the site, risk profile and response priorities"),
            ("Design", "Design camera coverage, storage and network architecture"),
            ("Deliver", "Install, configure and integrate the system"),
            ("Sustain", "Train your team and support ongoing performance"),
        ],
    },
    {
        "slug": "access-control",
        "title": "Access Control",
        "kicker": "Control the entry",
        "icon": "lock",
        "order": 2,
        "tags": "Biometrics, Turnstiles, Visitor flow",
        "summary": (
            "Make every entry intentional. From biometrics and card readers to visitor "
            "management, we create frictionless access without compromising control."
        ),
        "intro": (
            "A door is a decision point. We make that decision measurable - who was authorised, "
            "when they entered, and what happened next."
        ),
        "deliverables": "\n".join(
            [
                "Biometric, card and PIN terminals at controlled doors",
                "Turnstiles, speed gates and vehicle barriers",
                "Visitor management and temporary credential workflows",
                "Door hardware, controllers and centralised software integration",
            ]
        ),
        "outcomes": "\n".join(
            [
                "One authoritative record of who entered where, and when",
                "Entry that is fast for staff and impossible to improvise",
                "Roles, zones and reports your HR and security teams can both use",
            ]
        ),
        "meta_description": (
            "Biometric terminals, card readers, turnstiles and visitor management installed and "
            "integrated by a Nairobi access control company."
        ),
        "steps": [
            ("Map", "Walk every entry point and the people who legitimately use it"),
            ("Specify", "Choose credentials, readers, locks and software that fit the workflow"),
            ("Commission", "Install, test forced-entry and tailgating, then hand over drawings"),
            ("Support", "Manage roles, audits and expansions as the organisation changes"),
        ],
    },
    {
        "slug": "electric-fencing",
        "title": "Electric Fencing",
        "kicker": "Protect the perimeter",
        "icon": "fence",
        "image_caption": "Live-wire perimeter over a masonry wall",
        "order": 3,
        "tags": "Perimeter security, Alarm integration, Maintenance",
        "summary": (
            "A smart perimeter is your first line of defence. Our installations pair "
            "high-voltage protection with clean, discreet engineering and dependable alerts."
        ),
        "intro": (
            "The perimeter buys you time. Done well, it deters, detects and tells you exactly "
            "where attention is needed before anyone reaches a door."
        ),
        "deliverables": "\n".join(
            [
                "Compliant energisers, zone design and tamper monitoring",
                "Brackets, galvanised wiring and clean post alignment",
                "Alarm integration with cameras, lighting and control rooms",
                "Vegetation, insulation and performance maintenance visits",
            ]
        ),
        "outcomes": "\n".join(
            [
                "Zone-level alerts that responders can act on immediately",
                "A fence that still performs after rain, dust and seasons",
                "Documented test readings at handover and at every service visit",
            ]
        ),
        "meta_description": (
            "Electric fencing design, installation and maintenance in Kenya, integrated with "
            "CCTV, lighting and alarm monitoring."
        ),
        "steps": [
            ("Survey", "Measure the boundary and note ground conditions and risk zones"),
            ("Engineer", "Design energiser capacity, zones and mounting geometry"),
            ("Install", "Erect, energise and test each zone to specification"),
            ("Maintain", "Schedule checks so performance never quietly degrades"),
        ],
    },
    {
        "slug": "data-centre-construction",
        "title": "Data Centre Construction",
        "kicker": "Protect the core",
        "icon": "server",
        "order": 4,
        "tags": "Critical systems, Resilience, Build oversight",
        "summary": (
            "Build critical infrastructure with confidence. We support resilient, secure "
            "environments engineered for continuity, performance and future growth."
        ),
        "intro": (
            "A data centre is where physical security, power and cooling meet an uptime promise. "
            "We help you build it in the right order."
        ),
        "deliverables": "\n".join(
            [
                "Secure room design, containment and rack layout",
                "Power distribution, UPS and generator integration",
                "Environmental monitoring, fire detection and leak detection",
                "Structured cabling, access layers and commissioning documentation",
            ]
        ),
        "outcomes": "\n".join(
            [
                "An environment that tolerates a failure without losing service",
                "Clear as-built documentation for every discipline",
                "Headroom for growth that does not require a second rebuild",
            ]
        ),
        "meta_description": (
            "Data centre construction support in Kenya: secure rooms, power and cooling "
            "integration, environmental monitoring and commissioning."
        ),
        "steps": [
            ("Plan", "Define load, redundancy tier, growth and operating model"),
            ("Coordinate", "Work with civil, electrical and HVAC teams on a single drawing set"),
            ("Commission", "Test every failure path before go-live, not after"),
            ("Monitor", "Instrument the room so drift is visible early"),
        ],
    },
    {
        "slug": "security-risk-consultancy",
        "title": "Security Risk Consultancy",
        "kicker": "Advise with intent",
        "icon": "compass",
        "order": 5,
        "tags": "Risk reviews, Threat mapping, Advisory",
        "summary": (
            "Turn uncertainty into a clear action plan. Our specialists uncover vulnerabilities, "
            "prioritise risk and help leadership make decisive security investments."
        ),
        "intro": (
            "Advice is only useful when it can be funded, sequenced and defended in a board "
            "meeting. That is the standard we write to."
        ),
        "deliverables": "\n".join(
            [
                "Threat and vulnerability assessment across sites and functions",
                "Risk register with likelihood, impact and ownership",
                "Prioritised investment roadmap with phasing and budget bands",
                "Policy, procedure and control review for auditors",
            ]
        ),
        "outcomes": "\n".join(
            [
                "Leadership that can choose what to fund and why",
                "A defensible position for insurers, auditors and regulators",
                "Less spend on equipment that does not reduce the largest risks",
            ]
        ),
        "meta_description": (
            "Security risk consultancy in Kenya: threat mapping, risk registers and prioritised "
            "investment roadmaps for leadership teams."
        ),
        "steps": [
            ("Interview", "Understand assets, obligations and what keeps owners awake"),
            ("Analyse", "Map threats against current controls and real operating behaviour"),
            ("Recommend", "Rank risks and propose proportionate, costed responses"),
            ("Review", "Revisit assumptions as the organisation and threat landscape change"),
        ],
    },
    {
        "slug": "security-assessments",
        "title": "Security Assessments",
        "kicker": "Verify honestly",
        "icon": "clipboard",
        "order": 6,
        "tags": "Site audits, Gap analysis, Remediation",
        "summary": (
            "A sharper view of your security posture. We assess people, process and technology, "
            "then deliver practical recommendations that stand up in the real world."
        ),
        "intro": (
            "Systems that were right five years ago are often quietly wrong today. An assessment "
            "tells you which of them you can still rely on."
        ),
        "deliverables": "\n".join(
            [
                "Physical site audit with photographic evidence",
                "Camera, storage and network health verification",
                "Access credential review and orphaned-account cleanup",
                "Gap analysis with a practical remediation list",
            ]
        ),
        "outcomes": "\n".join(
            [
                "A short, honest list of what to fix first",
                "Confidence that blind spots are named rather than assumed",
                "A baseline you can measure the next audit against",
            ]
        ),
        "meta_description": (
            "Security assessments and site audits in Kenya covering people, process and "
            "technology, with practical remediation plans."
        ),
        "steps": [
            ("Inspect", "Walk the site and test controls as an adversary would"),
            ("Evidence", "Record findings with photos, logs and readings"),
            ("Report", "Grade each finding by risk and remediation effort"),
            ("Verify", "Return and confirm the fixes actually landed"),
        ],
    },
]

WHY_POINTS = [
    (
        "Solutions designed around your actual risk profile",
        "We start from what could realistically go wrong on your site, then choose the "
        "technology that answers it - not the other way around.",
    ),
    (
        "Quality equipment selected for Kenyan operating conditions",
        "Power instability, heat, dust and humidity are engineered for from the beginning, so "
        "systems keep performing after commissioning day.",
    ),
    (
        "Installation, integration and aftercare from one accountable team",
        "The people who specify the design carry it through installation and support, so nothing "
        "falls between contractors.",
    ),
    (
        "Evidence you can audit",
        "As-built drawings, IP plans, credential registers and test readings are handed over on "
        "completion and kept current.",
    ),
]

BRANDS = [
    ("IDEMIA", "idemia", "https://www.idemia.com/", "Biometric access", 1),
    ("Evolis", "evolis", "https://www.evolis.com/", "Card issuance", 2),
    ("Hikvision", "hikvision", "https://www.hikvision.com/", "Access terminals", 3),
    ("ZKTeco", "zkteco", "https://www.zkteco.com/", "Biometric & screening", 4),
    ("Entrust", "entrust", "https://www.entrust.com/", "Credential issuance", 5),
]

CATEGORIES = [
    ("Evolis card printers", "evolis-card-printers", "Direct-to-card and re-transfer ID card printers for desktop and high-volume issuance."),
    ("Evolis accessories", "evolis-accessories", "Consumables and modules that keep an ID programme dependable."),
    ("IDEMIA access control", "idemia-access-control", "Biometric terminals and centralised management for controlled entry."),
    ("Hikvision access control", "hikvision-access-control", "Multi-modal terminals and readers for modern workplace entry points."),
    ("Security screening", "security-screening", "Walk-through and handheld screening for controlled entrances."),
    ("Entrust issuance", "entrust-issuance", "Secure credential issuance and personalisation for identity programmes."),
    ("Hikvision video surveillance", "hikvision-video-surveillance", "Cameras and recording for continuous, reviewable visibility across a site."),
    ("ZKTeco access terminals", "zkteco-access-terminals", "Standalone and networked biometric terminals for doors, gates and attendance."),
]

PRODUCTS = [
    {
        "slug": "evolis-primacy-2",
        "title": "Evolis Primacy 2",
        "brand": "evolis",
        "category": "evolis-card-printers",
        "eyebrow": "Flexible desktop issuance",
        "order": 1,
        "is_featured": True,
        "summary": (
            "A direct-to-card printer for everyday ID programmes, with rewrite capability, "
            "encoding options and security-focused features."
        ),
        "body": (
            "Primacy 2 is the workhorse of a desktop ID programme: single-operator issuance of "
            "access credentials, visitor badges and staff ID cards. Rewrite capability means a "
            "mistake does not waste a card, and the encoding options let the same printer produce "
            "a credential that actually opens the doors it is printed for."
        ),
        "features": "\n".join(
            [
                "Print method: Direct-to-card, full colour",
                "Sides: Single-sided or dual-sided printing",
                "Card feed: Standard hopper, optional 100 / 200-card magazines",
                "Encoding: Contact, contactless, magnetic and UV security options",
                "Finishing: Optional hologram overlay and lamination module",
                "Duty cycle: Office and campus issuance volumes",
            ]
        ),
        "solutions": ["access-control"],
    },
    {
        "slug": "evolis-accessories",
        "title": "Evolis accessories",
        "brand": "evolis",
        "category": "evolis-accessories",
        "eyebrow": "Keep your issuance ready",
        "order": 2,
        "is_featured": True,
        "summary": (
            "The consumables and modules that make an ID programme dependable: ribbons, cards, "
            "cleaning kits, badge holders, encoders and lamination modules."
        ),
        "body": (
            "The consumables and modules that make an ID programme dependable: ribbons, cards, "
            "cleaning kits, badge holders, encoders and lamination modules. High Trust ribbons and "
            "plastic cards, cleaning kits and badge holders, CLM lamination module for selected printers."
        ),
        "features": "\n".join(
            [
                "High Trust ribbons and plastic cards",
                "Cleaning kits and badge holders",
                "CLM lamination module for selected printers",
            ]
        ),
        "solutions": ["access-control"],
    },
    {
        "slug": "evolis-cleaning-kits",
        "title": "Evolis cleaning kits",
        "brand": "evolis",
        "category": "evolis-accessories",
        "eyebrow": "Printer maintenance",
        "order": 3,
        "summary": (
            "Keep card printers performing consistently with manufacturer-aligned cleaning "
            "supplies for routine maintenance and print quality."
        ),
        "body": (
            "Keep card printers performing consistently with manufacturer-aligned cleaning supplies "
            "for routine maintenance and print quality. Adhesive cards and cleaning swabs, routine care "
            "for card printer rollers, use the kit matched to your printer model."
        ),
        "features": "\n".join(
            [
                "Adhesive cards and cleaning swabs",
                "Routine care for card printer rollers",
                "Use the kit matched to your printer model",
            ]
        ),
        "solutions": ["access-control"],
    },
    {
        "slug": "evolis-ymcko-ribbons",
        "title": "Evolis YMCKO ribbons",
        "brand": "evolis",
        "category": "evolis-accessories",
        "eyebrow": "Colour card consumables",
        "order": 4,
        "summary": (
            "YMCKO colour ribbons for producing crisp, professional ID cards on compatible "
            "Evolis printers."
        ),
        "body": (
            "YMCKO colour ribbons for producing crisp, professional ID cards on compatible Evolis "
            "printers. Yellow, magenta, cyan, black and overlay panels, designed for compatible "
            "Evolis printers, confirm ribbon code before ordering."
        ),
        "features": "\n".join(
            [
                "Yellow, magenta, cyan, black and overlay panels",
                "Designed for compatible Evolis printers",
                "Confirm ribbon code before ordering",
            ]
        ),
        "solutions": ["access-control"],
    },
    {
        "slug": "blank-pvc-cards",
        "title": "Blank PVC cards",
        "brand": "evolis",
        "category": "evolis-accessories",
        "eyebrow": "Card stock",
        "order": 5,
        "summary": (
            "Blank CR80 PVC cards ready for photo ID, visitor badges, membership cards and "
            "access credentials."
        ),
        "body": (
            "Blank CR80 PVC cards ready for photo ID, visitor badges, membership cards and access "
            "credentials. Standard credit-card format, suitable for compatible direct-to-card printers, "
            "available with optional slot or magnetic stripe configurations."
        ),
        "features": "\n".join(
            [
                "Standard credit-card format",
                "Suitable for compatible direct-to-card printers",
                "Available with optional slot or magnetic stripe configurations",
            ]
        ),
        "solutions": ["access-control"],
    },
    {
        "slug": "idemia-sigma-family",
        "title": "IDEMIA SIGMA family",
        "brand": "idemia",
        "category": "idemia-access-control",
        "eyebrow": "Biometric access control",
        "order": 6,
        "is_featured": True,
        "summary": (
            "Fingerprint access-control terminals for doors, turnstiles, server racks and "
            "demanding environments, with card and PIN options on supported models."
        ),
        "body": (
            "SIGMA terminals put biometric verification where the risk actually is - a plant room "
            "door, a server rack, a turnstile line. The family scales from a single controlled "
            "door to a multi-site estate managed centrally."
        ),
        "features": "\n".join(
            [
                "Verification: Fingerprint biometric, card and PIN options",
                "Deployment: Doors, turnstiles, racks and outdoor enclosures",
                "Management: Centralised enrolment and audit via MorphoManager",
                "Environment: Rated for dust, heat and high-traffic entry points",
            ]
        ),
        "solutions": ["access-control"],
    },
    {
        "slug": "morphomanager",
        "title": "MorphoManager",
        "brand": "idemia",
        "category": "idemia-access-control",
        "eyebrow": "Centralised management",
        "order": 7,
        "summary": (
            "Centralised management software for biometric access-control and "
            "time-and-attendance devices, with user administration, reporting and integrations."
        ),
        "body": (
            "One place to enrol people, define zones, run attendance reports and answer the "
            "question of who opened what. It turns a set of terminals into a managed system."
        ),
        "features": "\n".join(
            [
                "Administration: Users, credentials, zones and role-based permissions",
                "Reporting: Access events, attendance and audit exports",
                "Integration: Interfaces for HR, payroll and visitor systems",
                "Scale: Multi-site management with distributed terminals",
            ]
        ),
        "solutions": ["access-control", "security-assessments"],
    },
    {
        "slug": "hikvision-minmoe",
        "title": "Hikvision MinMoe",
        "brand": "hikvision",
        "category": "hikvision-access-control",
        "eyebrow": "Multi-modal terminals",
        "order": 8,
        "is_featured": True,
        "summary": (
            "Access-control and time-attendance terminals that combine biometric and credential "
            "options for modern workplace entry points."
        ),
        "body": (
            "MinMoe terminals are the pragmatic choice for office doors: fast face or fingerprint "
            "verification, a clean interface for staff, and single-door control without a separate "
            "controller in the ceiling."
        ),
        "features": "\n".join(
            [
                "Modes: Face, fingerprint, card and PIN on supported models",
                "Function: Terminal and controller in one unit for single-door sites",
                "Attendance: Time-and-attendance reporting built in",
                "Management: Central software and mobile app administration",
            ]
        ),
        "solutions": ["access-control"],
    },
    {
        "slug": "hikvision-card-readers",
        "title": "Hikvision card readers",
        "brand": "hikvision",
        "category": "hikvision-access-control",
        "eyebrow": "Credential readers",
        "order": 9,
        "summary": (
            "Compact readers for integrators pairing card credentials with controllers or "
            "terminal systems across commercial sites."
        ),
        "body": (
            "Sometimes a door only needs a badge. These readers give you a consistent credential "
            "experience across a commercial estate at the lowest cost per point."
        ),
        "features": "\n".join(
            [
                "Credential types: MIFARE, DESFire and HID options",
                "Interface: Wiegand and RS-485 to controllers",
                "Installation: Indoor surface and flush mounting",
            ]
        ),
        "solutions": ["access-control"],
    },
    {
        "slug": "walkthrough-detectors",
        "title": "Walkthrough metal detectors",
        "brand": "zkteco",
        "category": "security-screening",
        "eyebrow": "Security screening",
        "order": 10,
        "is_featured": True,
        "summary": (
            "Walkthrough metal-detector gates for controlled screening at entrances, campuses, "
            "commercial sites and events."
        ),
        "body": (
            "A screening gate sets the tone of an entrance. We size detection zones and sensitivity "
            "to the traffic so the queue moves and the alert still means something."
        ),
        "features": "\n".join(
            [
                "Zones: Multi-zone detection with location indication",
                "Throughput: Sized for lobby, campus and event traffic",
                "Integration: Pairs with CCTV overlay and handheld units",
                "Alerting: Audible and visual alarm with counted passes",
            ]
        ),
        "solutions": ["access-control", "security-assessments"],
    },
    {
        "slug": "entrust-sigma-ds2",
        "title": "Entrust Sigma DS2",
        "brand": "entrust",
        "category": "entrust-issuance",
        "eyebrow": "Secure dual-sided issuance",
        "order": 11,
        "is_featured": True,
        "summary": (
            "A dual-sided card printer and encoder for programmes that need verified identity "
            "credentials, not just printed badges."
        ),
        "body": (
            "When the card is also the key, issuance has to be controlled. The DS2 combines "
            "dual-sided printing with encoding so a credential is personalised and provisioned in "
            "one managed step."
        ),
        "features": "\n".join(
            [
                "Printing: Dual-sided, high-resolution monochrome and colour",
                "Encoding: Contact, contactless and magnetic provisioning",
                "Programme: Secure workflows for multi-site issuance",
            ]
        ),
        "solutions": ["access-control"],
    },
    {
        "slug": "hikvision-colorvu",
        "title": "Hikvision ColorVu",
        "brand": "hikvision",
        "category": "hikvision-video-surveillance",
        "eyebrow": "Full colour around the clock",
        "order": 12,
        "is_featured": True,
        "summary": (
            "Cameras that keep their picture in colour through the night, so clothing, vehicles "
            "and faces stay readable when the site is at its quietest."
        ),
        "body": (
            "A night-time review usually fails on colour, not on resolution. ColorVu carries its "
            "own warm fill light, so the record stays in colour from the moment the sun goes and "
            "the description a witness gives matches the footage."
        ),
        "features": "\n".join(
            [
                "Colour: Full-colour imaging day and night from a built-in fill light",
                "Low light: Large-aperture optics tuned for near-dark scenes",
                "Compression: H.265 coding to hold recording days down",
                "Analytics: Motion and perimeter events with false-alarm filtering",
                "Power: PoE or 12 V DC depending on model",
                "Forms: Bullet and turret housings for walls and eaves",
            ]
        ),
        "solutions": ["cctv-video-intelligence"],
    },
    {
        "slug": "hikvision-darkfighter",
        "title": "Hikvision DarkFighter",
        "brand": "hikvision",
        "category": "hikvision-video-surveillance",
        "eyebrow": "Detail in very low light",
        "order": 13,
        "summary": (
            "Low-light cameras for perimeters, yards and entrances where adding light is not an "
            "option and losing detail is."
        ),
        "body": (
            "Some boundaries cannot carry floodlights - neighbours, animals, blinding glare on a "
            "gate. DarkFighter holds usable detail on what ambient light there is, and falls back "
            "to a clean monochrome picture only when the scene truly runs out."
        ),
        "features": "\n".join(
            [
                "Sensor: Large-format sensor for low-light detail",
                "Colour: Colour at low illumination, monochrome at the floor",
                "Optics: Varifocal options across wide and telephoto fields",
                "Illumination: IR range matched to the scene",
                "Environment: Outdoor housings with wide dynamic range",
                "Analytics: Perimeter, counting and capture events by model",
            ]
        ),
        "solutions": ["cctv-video-intelligence"],
    },
    {
        "slug": "hikvision-turbo-hd",
        "title": "Hikvision Turbo HD",
        "brand": "hikvision",
        "category": "hikvision-video-surveillance",
        "eyebrow": "HD video over existing coax",
        "order": 14,
        "summary": (
            "Analogue-HD cameras and recorders for sites where the cable is already in the ground "
            "and only the picture is out of date."
        ),
        "body": (
            "The fastest way to a sharper record is usually the one that does not open the "
            "building. Turbo HD puts modern resolution down the coaxial cable an ageing analogue "
            "system already runs, so the upgrade is heads and a recorder, not a rewiring."
        ),
        "features": "\n".join(
            [
                "Cabling: Carries HD video over existing coaxial cable",
                "Retrofit: Replaces ageing analogue heads without reopening the fabric",
                "Resolution: Camera classes from general view to detail capture",
                "Recording: DVR channel counts sized to the site",
                "Remote: Live view and playback from the manufacturer's clients",
                "Mixed: IP heads supported on hybrid recorder models",
            ]
        ),
        "solutions": ["cctv-video-intelligence"],
    },
    {
        "slug": "hikvision-nvr",
        "title": "Hikvision network video recorders",
        "brand": "hikvision",
        "category": "hikvision-video-surveillance",
        "eyebrow": "Recording and review",
        "order": 15,
        "is_featured": True,
        "summary": (
            "The recorder holds the stream, the analytics and the evidence in one place - from a "
            "single shopfront to a multi-site estate."
        ),
        "body": (
            "Cameras only earn their keep if the footage is still there when it is asked for. We "
            "size channels, drives and retention to the review window a site actually needs, then "
            "set the archive so it survives the power cuts along with everything else."
        ),
        "features": "\n".join(
            [
                "Channels: Model ranges from small-site to estate counts",
                "Storage: Multi-bay enclosures, RAID options on larger series",
                "Retention: Sized to the site's review window, not a default",
                "Streams: H.265 coding with per-stream bitrate control",
                "Access: Front-panel UI, web client and remote viewing apps",
                "Openness: ONVIF profile support beside the manufacturer's protocol",
            ]
        ),
        "solutions": ["cctv-video-intelligence"],
    },
    {
        "slug": "idemia-visionpass",
        "title": "IDEMIA VisionPass",
        "brand": "idemia",
        "category": "idemia-access-control",
        "eyebrow": "Face-first entry",
        "order": 16,
        "is_featured": True,
        "summary": (
            "A face-recognition terminal that opens a door on a look, with liveness checks so a "
            "picture on a phone does not pass as a credential."
        ),
        "body": (
            "A face is the only credential people never forget, lose or lend. VisionPass verifies "
            "it at the door in ordinary light, and the liveness checks are what keep that "
            "convenience from becoming the weakness in the scheme."
        ),
        "features": "\n".join(
            [
                "Biometric: Face-first verification with liveness detection",
                "Modes: Standalone terminal, or reader behind an existing controller",
                "Tolerance: Works with glasses and everyday wearables",
                "Network: Ethernet and Wi-Fi on supported models",
                "Door hardware: Relay and Wiegand outputs on supported models",
                "Enrolment: Managed at reception or self-service by the door",
            ]
        ),
        "solutions": ["access-control"],
    },
    {
        "slug": "zkteco-f18",
        "title": "ZKTeco F18",
        "brand": "zkteco",
        "category": "zkteco-access-terminals",
        "eyebrow": "Standalone fingerprint access",
        "order": 17,
        "summary": (
            "A standalone fingerprint terminal for single doors and small sites that need access "
            "control without a server in the cupboard."
        ),
        "body": (
            "Not every site needs an enterprise platform. The F18 controls its own door, keeps its "
            "own record and still reports over the network when there is one to report to - which "
            "covers most offices, stores and back entrances."
        ),
        "features": "\n".join(
            [
                "Credential: Fingerprint verification, card and PIN options by model",
                "Deployment: Fully standalone, or networked over TCP/IP",
                "Control: Drives the lock relay and exit sensor",
                "Records: On-device event log for access and attendance",
                "Resilience: Battery backup holds the door and the log through outages",
                "Service: USB for enrolment, data capture and firmware",
            ]
        ),
        "solutions": ["access-control"],
    },
    {
        "slug": "zkteco-megaface",
        "title": "ZKTeco MegaFace series",
        "brand": "zkteco",
        "category": "zkteco-access-terminals",
        "eyebrow": "High-accuracy face verification",
        "order": 18,
        "summary": (
            "Facial terminals for entrances where people must be recognised at speed and at "
            "distance, without stopping to present anything."
        ),
        "body": (
            "A lobby door fails when the queue backs up behind it. These terminals read a face "
            "while the person is still walking, hold large template databases without slowing "
            "down, and double as the attendance record for the same badge."
        ),
        "features": "\n".join(
            [
                "Biometric: Face recognition tuned for busy entrances",
                "Distance: Recognises at walking range, with no pause at the reader",
                "Liveness: Rejects printed photos and screen replays",
                "Capacity: Large template databases for multi-site rollouts",
                "Modes: Access, attendance or both on one device",
                "Integration: Wiegand or relay output into existing hardware",
            ]
        ),
        "solutions": ["access-control"],
    },
    {
        "slug": "zkteco-handheld-metal-detectors",
        "title": "Handheld metal detectors",
        "brand": "zkteco",
        "category": "security-screening",
        "eyebrow": "Secondary screening",
        "order": 19,
        "summary": (
            "Handheld detectors that back up a screening gate, so an alarm is resolved at the "
            "entrance instead of argued about."
        ),
        "body": (
            "A gate tells you there is something; the wand tells you where. Handheld units keep "
            "the second pass quick and specific, which is what protects the queue as much as the "
            "lobby."
        ),
        "features": "\n".join(
            [
                "Use: Second-pass investigation after a gate alarm",
                "Sensitivity: Adjustable detection levels for the site",
                "Alerting: Audible, vibration and visual indication",
                "Endurance: Rechargeable operation across a shift on the door",
                "Pairing: Works alongside walkthrough gates and CCTV overlay",
                "Handling: Light body with a wrist strap for long queues",
            ]
        ),
        "solutions": ["access-control", "security-assessments"],
    },
    {
        "slug": "evolis-badgy-2",
        "title": "Evolis Badgy 2",
        "brand": "evolis",
        "category": "evolis-card-printers",
        "eyebrow": "Entry-level card issuance",
        "order": 20,
        "summary": (
            "A compact single-sided printer for teams issuing a few hundred cards a month who "
            "want the software to do most of the thinking."
        ),
        "body": (
            "Most small programmes do not need throughput; they need a card that looks like it "
            "came from the head office. Badgy 2 sits on a reception desk, ships with design and "
            "database tools, and consumes almost nothing between issues."
        ),
        "features": "\n".join(
            [
                "Print method: Direct-to-card, single-sided colour",
                "Footprint: Desktop-sized, for a reception or small office",
                "Volumes: Occasional and low-volume issuance",
                "Software: Card design and database tools bundled",
                "Consumables: Combined ribbon and cleaning cartridge",
                "Encoding: Contact and contactless options on supported models",
            ]
        ),
        "solutions": ["access-control"],
    },
    {
        "slug": "evolis-zenius",
        "title": "Evolis Zenius",
        "brand": "evolis",
        "category": "evolis-card-printers",
        "eyebrow": "Re-transfer desktop issuance",
        "order": 21,
        "is_featured": True,
        "summary": (
            "A re-transfer printer for credentials where finish and edge-to-edge coverage matter "
            "more than raw speed."
        ),
        "body": (
            "Re-transfer lays the image onto the card as a single film, so the face reaches the "
            "edge, the surface is flat and the print does not wear where a card is handled. It is "
            "the version of the printer you choose when the card is going to be looked at."
        ),
        "features": "\n".join(
            [
                "Print method: Re-transfer, edge-to-edge with a flat card face",
                "Durability: Image protected against flex and everyday wear",
                "Security: Overlay, hologram and UV options",
                "Encoding: Contact, contactless and magnetic modules",
                "Volumes: Office and programme issuance",
                "Supply: High-capacity ribbon options",
            ]
        ),
        "solutions": ["access-control"],
    },
    {
        "slug": "evolis-zenius-2",
        "title": "Evolis Zenius 2",
        "brand": "evolis",
        "category": "evolis-card-printers",
        "eyebrow": "Compact card issuance",
        "order": 22,
        "summary": (
            "A compact, user-friendly solution for single-sided printing of plastic cards, "
            "producing color or monochrome cards individually or in small runs."
        ),
        "body": (
            "Zenius 2 is a compact, user-friendly solution for single-sided printing of plastic cards, "
            "producing color or monochrome cards individually or in small runs. It features "
            "edge-to-edge output with a 300 dpi print head, manual or automatic card feeding, and "
            "is designed for everyday ID programmes."
        ),
        "features": "\n".join(
            [
                "Print method: Single-sided direct-to-card dye-sublimation/resin thermal-transfer",
                "Resolution: 300 dpi print head with edge-to-edge output",
                "Speed: Up to 150 color cards per hour",
                "Feeding: Manual or automatic with 50-card feeder and 20-card output hopper",
                "Software: Evolis Premium Suite software included",
                "Connectivity: USB/Ethernet with optional encoding modules on Expert version",
            ]
        ),
        "solutions": ["access-control"],
    },
    {
        "slug": "hikvision-ds-k1t671",
        "title": "Hikvision DS-K1T671 Pro Face Access Terminal",
        "brand": "hikvision",
        "category": "hikvision-access-control",
        "eyebrow": "Pro face access terminal",
        "order": 23,
        "summary": (
            "A Pro Series face-recognition terminal for access control and time-attendance applications, "
            "combining a 7-inch touch screen, wide-angle camera, deep-learning face recognition, "
            "and multiple authentication modes."
        ),
        "body": (
            "The DS-K1T671 is a Pro Series face-recognition terminal for access control and "
            "time-attendance applications. It combines a 7-inch touch screen, wide-angle camera, "
            "deep-learning face recognition with capacity for 6,000 faces, and multiple authentication "
            "modes including face anti-spoofing technology."
        ),
        "features": "\n".join(
            [
                "Display: 7-inch touch screen",
                "Camera: 2-megapixel wide-angle lens",
                "Capacity: 6,000 faces, 5,000 fingerprints, 50,000 events",
                "Algorithm: Deep-learning face recognition",
                "Security: Face anti-spoofing technology",
                "Lighting: Adjustable supplement light for dark environments",
            ]
        ),
        "solutions": ["access-control"],
    },
    {
        "slug": "zkteco-zk-d1090",
        "title": "ZKTeco ZK-D1090",
        "brand": "zkteco",
        "category": "security-screening",
        "eyebrow": "Security screening",
        "order": 24,
        "summary": (
            "A budget-friendly walk-through metal detector for schools, public venues, and corporate "
            "entrances, combining 9 detection zones, adjustable sensitivity, synchronized alerts, "
            "pedestrian counting, and anti-interference technology."
        ),
        "body": (
            "The ZK-D1090 is a budget-friendly walk-through metal detector designed for schools, "
            "public venues, and corporate entrances. It features 9 detection zones with adjustable "
            "configurations, 500 adjustable sensitivity levels, throughput of more than 40 persons "
            "per minute, and anti-interference technology."
        ),
        "features": "\n".join(
            [
                "Zones: 9 detection zones with adjustable configurations",
                "Sensitivity: 500 adjustable sensitivity levels",
                "Throughput: More than 40 persons per minute",
                "Display: 2.8-inch color screen with physical keypad",
                "Counting: Pedestrian and alarm counts",
                "Alerts: Synchronized LED and audio alerts",
            ]
        ),
        "solutions": ["access-control", "security-assessments"],
    },
    {
        "slug": "evolis-quantum",
        "title": "Evolis Quantum",
        "brand": "evolis",
        "category": "evolis-card-printers",
        "eyebrow": "High-volume card issuance",
        "order": 25,
        "is_featured": True,
        "summary": (
            "A high-volume card printer for printing and encoding plastic cards. It personalizes "
            "cards front and back, in color or monochrome, and combines desktop-printer flexibility "
            "with centralized production capability."
        ),
        "body": (
            "Quantum is a high-volume card printer for printing and encoding plastic cards. It "
            "personalizes cards front and back, in color or monochrome, combining desktop-printer "
            "flexibility with centralized production capability. It features more than 1,000 cards "
            "per hour in monochrome and more than 150 cards per hour in color."
        ),
        "features": "\n".join(
            [
                "Speed: More than 1,000 cards per hour in monochrome, 150+ in color",
                "Printing: Front-and-back personalization in color or monochrome",
                "Encoding: Encode and print cards in a single pass",
                "Modules: Removable module for magnetic, contact smart-card, and contactless encoding",
                "Hoppers: Interchangeable 500-card input and output hoppers",
                "Connectivity: USB and Ethernet interfaces",
            ]
        ),
        "solutions": ["access-control"],
    },
    {
        "slug": "entrust-sigma-ds3",
        "title": "Entrust Sigma DS3",
        "brand": "entrust",
        "category": "entrust-issuance",
        "eyebrow": "Programme-scale issuance",
        "order": 26,
        "is_featured": True,
        "summary": (
            "A dual-sided printer and encoder for credential programmes that print, provision and "
            "verify across more than one site."
        ),
        "body": (
            "Once issuance is spread over several locations, the risk is not the print - it is the "
            "card that was encoded against the wrong record. The DS3 family keeps printing, "
            "encoding and verification in one managed pass, so a credential leaves the desk "
            "already correct."
        ),
        "features": "\n".join(
            [
                "Printing: Dual-sided colour and monochrome",
                "Encoding: Contact, contactless and magnetic in one pass",
                "Workflow: Multi-site issuance under central control",
                "Quality: Automated calibration and verification checks",
                "Supply: High-capacity card magazines and ribbons",
                "Programme: Managed alongside the credentials it issues",
            ]
        ),
        "solutions": ["access-control"],
    },
]

CASE_STUDIES = [
    {
        "slug": "quest-group",
        "client": "Quest Group",
        "title": "Security and data infrastructure for Quest Group",
        "sector": "Commercial property",
        "country": "Kenya",
        "eyebrow": "Security & data infrastructure",
        "order": 1,
        "is_featured": True,
        "published_on": datetime.date(2025, 9, 30),
        "summary": (
            "Right Point Solutions installed security and data infrastructure for Quest Group, "
            "bringing dependable protection and connected systems together for their operating "
            "environment."
        ),
        "challenge": (
            "The site needed protection and connectivity treated as one brief. Camera coverage, "
            "controlled entry and the data infrastructure behind them had been specified "
            "separately, which left gaps nobody owned."
        ),
        "approach": (
            "We designed the security and data layers together - camera placement against real "
            "circulation routes, controlled entry at the points that matter, and a structured "
            "cabling and storage backbone that both systems rely on. Installation was sequenced "
            "around live operations so the site never went dark."
        ),
        "result": (
            "One connected system, documented handover, and a single team responsible for "
            "performance afterwards. The operators gained coverage they could trust without "
            "adding headcount."
        ),
        "highlights": "\n".join(
            [
                "Connected security and data layers",
                "Installation aligned to the operating environment",
                "One accountable delivery partner",
            ]
        ),
    },
    {
        "slug": "ibs-bank-somalia",
        "client": "IBS Bank Somalia",
        "title": "Access control installation for IBS Bank Somalia",
        "sector": "Banking",
        "country": "Somalia",
        "eyebrow": "Access control installation",
        "order": 2,
        "is_featured": True,
        "published_on": datetime.date(2025, 6, 30),
        "summary": (
            "Right Point Solutions delivered access control for IBS Bank Somalia, helping "
            "strengthen controlled entry and day-to-day security across their banking environment."
        ),
        "challenge": (
            "A banking environment needs entry that is auditable by default: staff areas, cash "
            "handling zones and customer-facing doors each carry a different rule, and every "
            "exception has to be visible."
        ),
        "approach": (
            "We specified credential-led access workflows per zone, enrolled users against clear "
            "roles, and installed terminals and locking hardware suited to the building's traffic "
            "and operating hours."
        ),
        "result": (
            "Controlled entry points with reporting the security team actually reads, and a "
            "handover that let branch staff manage day-to-day changes themselves."
        ),
        "highlights": "\n".join(
            [
                "Controlled entry points",
                "Credential-led access workflows",
                "Practical installation and handover",
            ]
        ),
    },
    # The four profiles below carry placeholder wording at discipline level only - no
    # counts, dates or site specifics. Replace them with the real brief before publishing.
    {
        "slug": "elimu-sacco",
        "client": "Elimu Sacco",
        "title": "Security systems for Elimu Sacco",
        "sector": "SACCO",
        "country": "Kenya",
        "eyebrow": "Premises security",
        "order": 3,
        "summary": (
            "Right Point Solutions works with Elimu Sacco on the security and connected "
            "systems that keep their premises and daily operations running."
        ),
        "challenge": (
            "A SACCO counter is a public space with private value behind it: staff, members "
            "and cash move through the same doors, so entry, oversight and record-keeping "
            "have to hold together without slowing service down."
        ),
        "approach": (
            "We look at the site as one system - where people are allowed, what needs to be "
            "seen, and what has to be recoverable afterwards - then install and document it "
            "so the team on site can run it themselves."
        ),
        "result": (
            "Working coverage and controlled entry, handed over with the records and support "
            "that keep it reliable after installation."
        ),
        "highlights": "\n".join(
            [
                "Premises security and oversight",
                "Controlled entry for staff areas",
                "Installation with documented handover",
            ]
        ),
    },
    {
        "slug": "synthesis-kenya",
        "client": "Synthesis Kenya Limited",
        "title": "Security systems for Synthesis Kenya Limited",
        "sector": "Architecture & development",
        "country": "Kenya",
        "eyebrow": "Premises security",
        "order": 4,
        "summary": (
            "Right Point Solutions works with Synthesis Kenya Limited on security and "
            "connected infrastructure across their working environment."
        ),
        "challenge": (
            "A studio environment is judged by the way it works: open space, models and "
            "equipment on the tables, clients coming and going, and drawings and data that "
            "have to stay private. Protection had to work without turning the office into a "
            "checkpoint."
        ),
        "approach": (
            "Coverage and controlled entry are placed around real movement - who uses which "
            "space and when - with the cabling and storage behind them specified at the same "
            "time rather than bolted on afterwards."
        ),
        "result": (
            "One connected setup with clear ownership, documented handover and support that "
            "continues after installation."
        ),
        "highlights": "\n".join(
            [
                "Coverage and controlled entry together",
                "Structured cabling and storage backbone",
                "One accountable delivery partner",
            ]
        ),
    },
    {
        "slug": "teetop-shop",
        "client": "Teetop Shop",
        "title": "Security systems for Teetop Shop",
        "sector": "",
        "country": "Kenya",
        "eyebrow": "Client reference",
        "order": 5,
        "summary": (
            "Right Point Solutions works with Teetop Shop on the security systems that "
            "support their trading environment."
        ),
        "challenge": (
            "A trading space is judged by the customer's experience, so protection has to "
            "work quietly - stock and staff covered, sightlines kept open, and nothing that "
            "feels like a barrier at the till."
        ),
        "approach": (
            "Cameras are placed against real floor routes and blind spots, entry is "
            "controlled where stock and cash are held, and the system is set up so "
            "day-to-day checks take seconds rather than training."
        ),
        "result": (
            "A trading floor that stays open and observable, with evidence available when it "
            "is needed and a team that can use the system without support."
        ),
        "highlights": "\n".join(
            [
                "Floor coverage without obstructing service",
                "Controlled back-of-house entry",
                "Practical day-to-day operation",
            ]
        ),
    },
    {
        "slug": "fincom-africa",
        "client": "Fincom Africa",
        "title": "Security systems for Fincom Africa",
        "sector": "ICT services",
        "country": "Kenya",
        "eyebrow": "Security & controlled entry",
        "order": 6,
        "summary": (
            "Right Point Solutions works with Fincom Africa on security, controlled entry "
            "and connected infrastructure for their operations."
        ),
        "challenge": (
            "An ICT operation keeps its own kit and its clients' data on site. That makes "
            "the equipment the asset: entry has to be traceable by person and zone, and the "
            "room that holds it has to stay cool, powered and observed."
        ),
        "approach": (
            "We separate the site into zones, assign entry rules and credentials per role, "
            "and back that with coverage and network capacity sized to the reporting the "
            "team actually needs."
        ),
        "result": (
            "Controlled, reportable entry with visible coverage, and a handover that lets "
            "staff manage routine changes themselves."
        ),
        "highlights": "\n".join(
            [
                "Zone-based controlled entry",
                "Coverage with retrievable evidence",
                "Reporting and handover staff can use",
            ]
        ),
    },
]


class Command(BaseCommand):
    help = "Create or update Right Point Solutions content in the database."

    def add_arguments(self, parser):
        parser.add_argument(
            "--skip-products", action="store_true", help="Only seed settings, solutions and case studies."
        )

    @transaction.atomic
    def handle(self, *args, **options):
        setting = SiteSetting.load()
        self.stdout.write(f"Site settings: {setting.company_name}")

        for index, payload in enumerate(SOLUTIONS, start=1):
            steps = payload.pop("steps")
            meta = dict(payload)
            meta["order"] = meta.get("order", index)
            solution, _created = Solution.objects.update_or_create(
                slug=meta.pop("slug"), defaults=meta
            )
            ProcessStep.objects.filter(solution=solution).delete()
            for step_order, (label, description) in enumerate(steps, start=1):
                ProcessStep.objects.create(
                    solution=solution, label=label, description=description, order=step_order
                )
        self.stdout.write(self.style.SUCCESS(f"Solutions: {len(SOLUTIONS)} upserted"))

        for order, (title, description) in enumerate(WHY_POINTS, start=1):
            WhyPoint.objects.update_or_create(
                title=title, defaults={"description": description, "order": order}
            )
        self.stdout.write(self.style.SUCCESS(f"Why points: {len(WHY_POINTS)} upserted"))

        for study in CASE_STUDIES:
            payload = dict(study)
            slug = payload.pop("slug")
            CaseStudy.objects.update_or_create(slug=slug, defaults=payload)
        self.stdout.write(self.style.SUCCESS(f"Case studies: {len(CASE_STUDIES)} upserted"))

        if options.get("skip_products"):
            return

        for name, slug, website, speciality, order in BRANDS:
            Brand.objects.update_or_create(
                slug=slug,
                defaults={"name": name, "website": website, "speciality": speciality, "order": order},
            )
        for name, slug, description in CATEGORIES:
            ProductCategory.objects.update_or_create(
                slug=slug, defaults={"name": name, "description": description}
            )
        for product in PRODUCTS:
            payload = dict(product)
            slug = payload.pop("slug")
            brand = Brand.objects.get(slug=payload.pop("brand"))
            category = ProductCategory.objects.get(slug=payload.pop("category"))
            solution_slugs = payload.pop("solutions", [])
            payload.update({"brand": brand, "category": category})
            record, _created = Product.objects.update_or_create(slug=slug, defaults=payload)
            record.solutions.set(Solution.objects.filter(slug__in=solution_slugs))
        self.stdout.write(
            self.style.SUCCESS(
                f"Catalogue: {Brand.objects.count()} brands, {ProductCategory.objects.count()} "
                f"categories, {Product.objects.count()} products"
            )
        )
