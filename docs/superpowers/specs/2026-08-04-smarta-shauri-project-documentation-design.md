# Smarta Shauri Project Documentation Design

**Date:** 4 August 2026  
**Status:** Approved for production  
**Deliverable:** Editable Microsoft Word document (`.docx`) suitable for Google Docs

## Purpose

Create a concise, non-technical academic Project Documentation for Smarta Shauri. The report will explain the project in approximately five content pages and use the remaining pages for a carefully selected visual record of the most important system functions.

The document is different from the User Manual: it describes the project problem, purpose, scope, users, database, development approach, results and limitations, while screenshots demonstrate the implemented outcome.

## Audience and tone

- Primary audience: university supervisor, course instructor and project assessors.
- Secondary audience: non-technical readers interested in the system.
- Language: formal, clear and accessible.
- Technical depth: brief explanations only; no source code, endpoint listings, database schema or detailed deployment instructions.
- Claims must match the implemented system and identify advisory or historical information clearly.

## Required formatting

- Page size: US Letter, portrait.
- Margins: 1 inch on all sides.
- Body font: Times New Roman, 12 point.
- Body line spacing: 1.5.
- Body alignment: justified.
- Heading font: Times New Roman, bold, larger than body text.
- Figure captions and explanatory text: Times New Roman, 12 point.
- Footer: document title and page number.
- Total length: exactly 17 pages.
- Output remains editable in Microsoft Word and Google Docs.

## Cover information

**UNIVERSITY OF EASTERN AFRICA, BARATON**  
**SCHOOL OF BUSINESS**  
**DEPARTMENT OF INFORMATION SYSTEMS AND COMPUTING**

**Course:** INSY492 - Senior Project  
**Student name:** BENSIDNEY NDUNG'U  
**Student ID:** SNDUBE2311  
**Course instructor:** OMARI DICKSON  
**Supervisor:** OMARI DICKSON  
**Submission date:** 17 March 2026

Document title: **SMARTA SHAURI PROJECT DOCUMENTATION**  
Subtitle: **CBC-Aligned Career Guidance System**

## Approved 17-page structure

1. Formal university cover page.
2. Project overview and objectives.
3. Problem statement and project justification.
4. Project scope and major features.
5. User roles and responsibilities.
6. Simple system and database overview, development approach, testing, limitations and conclusion.
7. Public homepage and registration.
8. Student dashboard and profile.
9. Grades and academic progress.
10. RIASEC assessment and career profile.
11. Institution and programme search.
12. Subject-combination exploration and comparison.
13. Learner plan and parent access.
14. Parent dashboard and learner summary.
15. Counsellor dashboard and learner review.
16. School-administrator dashboard and offerings.
17. System-administrator dashboard and catalogue.

## Narrative content

### Project overview and objectives

Explain Smarta Shauri as a Progressive Web Application for CBC-aligned career guidance in Central Kenya. Include the three approved objectives covering PWA guidance, RIASEC-based assessment, and searchable institution/programme information.

### Problem and justification

Explain the challenge of learners making Senior School pathway and career decisions with scattered information, limited personalized guidance, and unequal access to counsellors. Describe why a mobile-friendly advisory platform is useful without presenting it as a replacement for official Ministry or institution services.

### Scope and features

Summarize registration, profiles, grades, academic progress, RIASEC assessment, pathway recommendations, subject-combination exploration, education goals, parent access, counsellor support, school administration, system administration, notifications and reports.

### User roles

Give clear, brief descriptions for student, parent, counsellor, school administrator and system administrator. State the main information or actions available to each role and respect role-based privacy boundaries.

### System and database overview

Explain in plain language that the web interface connects to a Django application and a MySQL database. The database stores user accounts, learner profiles, grades, assessment responses/results, school and programme information, plans, notifications and audit records. Mention that role permissions protect access. Do not include database tables, SQL, API endpoints or infrastructure configuration.

### Development, testing, limitations and conclusion

Describe iterative development and testing in general terms. State that the system was tested across the major roles and workflows. Include concise limitations: guidance is advisory, official criteria must be confirmed, coverage depends on current catalogue data, internet access is needed for most functions, and the pilot focuses on five Central Kenya counties. End with the expected benefit to learners and guidance teams.

## Screenshot policy

- Use no more than 22 important screenshots selected from the verified User Manual assets, reducing the visual set by more than half from the full User Manual.
- Use one or two large screenshots per page.
- Place screenshot pages after the five narrative pages.
- Every screenshot must have a figure number, descriptive caption and one short paragraph explaining what the figure demonstrates.
- Preserve legibility; crop to the relevant interface region when necessary.
- Do not include passwords, tokens, private counsellor notes or unnecessary personal information.
- Reuse verified screenshots rather than recapturing unchanged pages.

## Selected screenshot set

1. Public homepage.
2. Registration.
3. Student dashboard.
4. Student profile.
5. Grades.
6. Academic progress.
7. RIASEC questionnaire.
8. Career profile/results.
9. Institution search.
10. Programme catalogue or entry-requirement reference.
11. Explore Choices.
12. Compare Choices.
13. Learner plan.
14. Parent access.
15. Parent dashboard.
16. Learner summary.
17. Counsellor dashboard.
18. Counsellor learner detail.
19. School-administrator dashboard.
20. School offerings.
21. System-administrator dashboard.
22. System catalogue.

The builder may use a maximum of two screenshots on a page and may omit one screenshot from a pair if necessary to preserve readability and the exact 17-page limit.

## Verification and acceptance criteria

- The final Word document opens and remains editable.
- The latest render contains exactly 17 pages.
- Times New Roman 12-point body text and 1.5 line spacing are encoded in document styles.
- Pages 2-6 remain concise and non-technical.
- Page 5 clearly distinguishes all five user roles.
- Page 6 contains a short, accurate MySQL database explanation.
- Pages 7-17 contain only selected important screenshots with captions and explanations.
- Every rendered page is inspected at full detail and contains no clipping, overlap, broken image, awkward page break or unreadable caption.
- No unsupported feature claim or sensitive credential appears.
