"""
DHARMA-NYAYA — Pre-translate all quiz questions into all supported languages.
Stores results in SQLite (quiz_translations.db) for instant loading.

Usage:
    python translate_quiz.py
"""

import asyncio
import json
import sqlite3
import os
import sys

# Ensure app is importable
sys.path.insert(0, os.path.dirname(__file__))

from app.services.gemma_service import gemma_service
from app.models.schemas import LANGUAGE_NAMES
from app.core.config import get_settings

# ── Quiz Bank (same as quiz.js) ────────────────────────────────────────────

QUIZ_BANK = {
    "fundamental_rights": [
        {"q": "What is the minimum age for voting in India?", "opts": ["16 years", "18 years", "21 years", "25 years"], "ans": 1, "explain": "Under Article 326 of the Constitution, every Indian citizen who is 18 years or older has the right to vote, regardless of caste, religion, or gender."},
        {"q": "Which Article of the Indian Constitution abolishes 'untouchability'?", "opts": ["Article 14", "Article 17", "Article 21", "Article 25"], "ans": 1, "explain": "Article 17 abolishes untouchability and declares its practice in any form as a punishable offense under the Protection of Civil Rights Act, 1955."},
        {"q": "Right to Education is guaranteed under which Article?", "opts": ["Article 19", "Article 21", "Article 21A", "Article 24"], "ans": 2, "explain": "Article 21A (inserted by 86th Amendment, 2002) makes free and compulsory education a Fundamental Right for children aged 6-14 years."},
        {"q": "Can Fundamental Rights be suspended during a National Emergency?", "opts": ["Never", "Only Article 19", "All except Article 20 & 21", "All of them"], "ans": 2, "explain": "During a National Emergency under Article 352, Fundamental Rights under Article 19 are automatically suspended. However, the right to life (Art. 20 & 21) can NEVER be suspended — even during emergency."},
        {"q": "Which Fundamental Right protects you from illegal arrest?", "opts": ["Article 14", "Article 19", "Article 21", "Article 22"], "ans": 3, "explain": "Article 22 provides protection against arrest and detention. Every arrested person must be informed of the grounds of arrest, produced before a magistrate within 24 hours, and has the right to consult a lawyer."},
        {"q": "Who can file a PIL (Public Interest Litigation) in India?", "opts": ["Only the affected person", "Only lawyers", "Any citizen", "Only government"], "ans": 2, "explain": "Any public-spirited citizen can file a PIL in the High Court or Supreme Court under Article 226 or 32 respectively. This is a powerful tool to address issues affecting the public at large."},
        {"q": "Article 15 prohibits discrimination on the grounds of:", "opts": ["Only religion", "Religion and caste", "Religion, race, caste, sex, place of birth", "Only caste and sex"], "ans": 2, "explain": "Article 15 prohibits discrimination on grounds of religion, race, caste, sex, or place of birth. The State shall not discriminate in access to public places, facilities, and services."},
    ],
    "police_rights": [
        {"q": "Can police arrest you without a warrant?", "opts": ["Yes, for any offense", "Yes, but only for cognizable offenses", "No, never", "Only with court permission"], "ans": 1, "explain": "Police can arrest without a warrant only for cognizable offenses (serious crimes like theft, robbery, murder). For non-cognizable offenses (minor), they need a magistrate's order."},
        {"q": "Within how many hours must an arrested person be produced before a magistrate?", "opts": ["12 hours", "24 hours", "48 hours", "72 hours"], "ans": 1, "explain": "Under Article 22(2) of the Constitution and Section 57 of CrPC, every arrested person must be produced before the nearest magistrate within 24 hours (excluding travel time)."},
        {"q": "Can a woman be arrested after sunset and before sunrise?", "opts": ["Yes, anytime", "No, except by a female officer with magistrate order", "Only with two witnesses", "Only for serious crimes"], "ans": 1, "explain": "Under Section 46(4) CrPC, a woman cannot be arrested after sunset and before sunrise unless in exceptional circumstances, and only by a female police officer with prior permission of a Judicial Magistrate."},
        {"q": "Is it legal for police to detain you for more than 24 hours without a formal charge?", "opts": ["Yes, up to 15 days", "Yes, if investigation is pending", "No, it is illegal", "Only for terrorism cases"], "ans": 2, "explain": "Detention beyond 24 hours without producing before a magistrate is ILLEGAL under Article 22. If police don't file charges, you must be released. This is a Fundamental Right."},
        {"q": "What should you do first when arrested?", "opts": ["Resist the arrest", "Ask for the reason of arrest", "Run away", "Call a politician"], "ans": 1, "explain": "Under Section 50 CrPC, every arrested person has the RIGHT to know the grounds of arrest. Ask for the reason, note the officer's name and badge number, and request to inform a family member."},
        {"q": "Can police take your confession and use it in court?", "opts": ["Yes, always", "Yes, if recorded on video", "No, confessions to police are not admissible", "Only in lower courts"], "ans": 2, "explain": "Under Section 25 of the Indian Evidence Act, a confession made to a police officer is NOT admissible as evidence in court. Only confessions made before a Judicial Magistrate (under Section 164 CrPC) are valid."},
    ],
    "women_rights": [
        {"q": "What is the punishment for dowry demand under the Dowry Prohibition Act?", "opts": ["Fine only", "Up to 5 years imprisonment", "Warning letter", "Community service"], "ans": 1, "explain": "Under the Dowry Prohibition Act 1961, giving or taking dowry is punishable with imprisonment of minimum 5 years and a fine of ₹15,000 or the value of dowry, whichever is higher."},
        {"q": "Under which Act can a woman file a complaint for workplace sexual harassment?", "opts": ["IPC Section 354", "POSH Act 2013", "Domestic Violence Act", "Equal Remuneration Act"], "ans": 1, "explain": "The POSH Act (Prevention of Sexual Harassment at Workplace) 2013 requires every organization with 10+ employees to form an Internal Complaints Committee. Complaints must be resolved within 90 days."},
        {"q": "Can a woman file an FIR at any police station, regardless of where the crime occurred?", "opts": ["No, only at local station", "Yes, Zero FIR can be filed anywhere", "Only at women's police station", "Only at the district HQ"], "ans": 1, "explain": "A Zero FIR can be filed at ANY police station regardless of jurisdiction. The FIR is then transferred to the appropriate police station. This is especially important in emergency situations."},
        {"q": "Under the Domestic Violence Act, who is considered an 'aggrieved person'?", "opts": ["Only the wife", "Only women", "Any woman in a domestic relationship", "Anyone in the household"], "ans": 2, "explain": "Under the Protection of Women from Domestic Violence Act 2005, any woman in a domestic relationship (wife, live-in partner, mother, sister, daughter) who faces physical, emotional, sexual, or economic abuse can seek protection."},
        {"q": "What is the legal age of marriage for women in India?", "opts": ["16 years", "18 years", "21 years", "No minimum age"], "ans": 1, "explain": "The legal age of marriage is 18 years for women and 21 years for men. Child marriage is punishable under the Prohibition of Child Marriage Act 2006 with up to 2 years imprisonment and ₹1 lakh fine."},
        {"q": "Is stalking a criminal offense in India?", "opts": ["No, it is not recognized", "Yes, under IPC Section 354D", "Only if physical contact occurs", "Only for repeat offenses"], "ans": 1, "explain": "Stalking is a criminal offense under Section 354D IPC (now BNS Section 78). First offense: up to 3 years imprisonment. Repeat offense: up to 5 years. This includes both physical and cyber stalking."},
    ],
    "consumer_rights": [
        {"q": "Within how many days can you file a consumer complaint after purchase?", "opts": ["30 days", "6 months", "1 year", "2 years"], "ans": 3, "explain": "Under the Consumer Protection Act 2019, a consumer complaint must be filed within 2 years from the date the cause of action arises. However, the court may allow late filing if there is sufficient cause for delay."},
        {"q": "What is the monetary limit for filing at a District Consumer Forum?", "opts": ["Up to ₹20 lakh", "Up to ₹50 lakh", "Up to ₹1 crore", "No limit"], "ans": 2, "explain": "Under the Consumer Protection Act 2019: District Commission handles claims up to ₹50 lakh, State Commission up to ₹2 crore, and National Commission above ₹2 crore."},
        {"q": "Is a bill/receipt mandatory for filing a consumer complaint?", "opts": ["Yes, always", "No, other evidence works too", "Only for electronics", "Only above ₹500"], "ans": 1, "explain": "While a bill strengthens your case, it is NOT mandatory. You can also use bank statements, warranty cards, photographs, emails, chat screenshots, or witness testimony as evidence."},
        {"q": "Can you file a consumer complaint online?", "opts": ["No, must visit in person", "Yes, through e-Daakhil portal", "Only through a lawyer", "Only for government services"], "ans": 1, "explain": "The e-Daakhil portal (edaakhil.nic.in) allows you to file consumer complaints online from anywhere in India. The fee is nominal (₹100-₹5000 depending on claim amount) and can be paid online."},
        {"q": "MRP (Maximum Retail Price) includes which taxes?", "opts": ["No taxes", "Only GST", "All taxes including GST", "Only state taxes"], "ans": 2, "explain": "MRP is the maximum price inclusive of ALL taxes (including GST). No shopkeeper can charge above MRP. If you're charged more, it's a violation of the Legal Metrology Act and you can file a complaint."},
    ],
    "property_rights": [
        {"q": "Is registration of a property sale deed mandatory?", "opts": ["No, verbal agreement is enough", "Only for properties above ₹100", "Yes, under the Registration Act", "Only in urban areas"], "ans": 2, "explain": "Under Section 17 of the Registration Act 1908, registration is mandatory for all property transactions involving immovable property worth more than ₹100. Unregistered sale deeds cannot be used as evidence of transfer."},
        {"q": "Can a tenant be evicted without a court order?", "opts": ["Yes, if rent is overdue", "Yes, with 1 month notice", "No, only through court order", "Only by police"], "ans": 2, "explain": "Under various Rent Control Acts, a landlord CANNOT evict a tenant without a court order, even if rent is overdue. Self-help eviction (changing locks, cutting utilities) is ILLEGAL and actionable."},
        {"q": "Do daughters have equal right to ancestral property?", "opts": ["No, only sons", "Yes, since the Hindu Succession Amendment 2005", "Only if unmarried", "Only if father agrees"], "ans": 1, "explain": "Since the Hindu Succession (Amendment) Act 2005, daughters have EQUAL coparcenary rights in ancestral property as sons. This applies even if the father died before 2005, as clarified by the Supreme Court in 2020."},
        {"q": "What is the stamp duty for property registration?", "opts": ["Fixed at 1%", "Varies by state, typically 4-8%", "No stamp duty required", "Only 2% for women"], "ans": 1, "explain": "Stamp duty varies by state (typically 4-8% of property value). Many states offer reduced rates for women buyers (often 1-2% less). Always check your state's current rates before registration."},
        {"q": "Can a landlord increase rent arbitrarily?", "opts": ["Yes, anytime", "No, governed by Rent Control Act", "Only once a year", "Only with tenant consent"], "ans": 1, "explain": "Under Rent Control Acts, landlords cannot increase rent beyond the prescribed percentage (usually 5-10% per year). Any increase beyond this or without proper notice is illegal. Tenants can challenge arbitrary increases."},
    ],
    "labour_rights": [
        {"q": "What is the current national minimum wage in India?", "opts": ["₹100/day", "₹176/day", "₹300/day", "₹500/day"], "ans": 1, "explain": "The national floor-level minimum wage is ₹176/day (revised periodically). However, actual minimum wages vary by state and skill level. Many states have higher minimum wages than the national floor."},
        {"q": "Maximum working hours per week under the Factories Act?", "opts": ["40 hours", "48 hours", "56 hours", "60 hours"], "ans": 1, "explain": "Under Section 51 of the Factories Act 1948, no adult worker shall work more than 48 hours per week and 9 hours per day. Overtime work must be paid at double the normal wage rate."},
        {"q": "Is EPF (Provident Fund) mandatory for all employees?", "opts": ["Yes, all employees", "Only for companies with 20+ employees", "Only government jobs", "Only if salary > ₹25,000"], "ans": 1, "explain": "Under the EPF Act, EPF is mandatory for establishments with 20 or more employees. Both employer and employee contribute 12% of basic salary. Employees earning above ₹15,000/month can opt out but usually don't."},
        {"q": "Can an employer terminate you without notice?", "opts": ["Yes, immediately", "After 1 day notice", "No, notice period or salary in lieu is required", "Only during probation"], "ans": 2, "explain": "Under the Industrial Disputes Act, no employer can terminate a worker who has been in continuous service for 1+ year without 1 month's written notice (or wages in lieu), and prior approval of the appropriate government for establishments with 100+ workers."},
        {"q": "Is maternity leave a legal right?", "opts": ["No, it's company policy", "Yes, 12 weeks under law", "Yes, 26 weeks under the Maternity Benefit Act", "Only in government jobs"], "ans": 2, "explain": "The Maternity Benefit (Amendment) Act 2017 provides 26 weeks of paid maternity leave for the first two children, and 12 weeks for subsequent children. This applies to all establishments with 10+ employees."},
        {"q": "What is Gratuity and when is it payable?", "opts": ["Bonus paid monthly", "Payment after 5 years of service", "Yearly bonus", "Retirement pension"], "ans": 1, "explain": "Under the Payment of Gratuity Act 1972, gratuity is payable after 5 years of continuous service upon retirement, resignation, or death. Calculation: (15 × last drawn salary × years of service) / 26. Maximum limit is ₹20 lakh."},
    ],
}

# ── Ukrainian Quiz Bank — all questions in Ukrainian (права у країнах ЄС) ──
UKRAINIAN_QUIZ_BANK = {
    "uk_temporary_protection": [
        {"q": "Згідно з Директивою ЄС про тимчасовий захист, на який початковий термін надається тимчасовий захист українським біженцям?", "opts": ["3 місяці", "1 рік", "3 роки", "Безстроково"], "ans": 1, "explain": "Тимчасовий захист відповідно до Директиви Ради ЄС 2001/55/ЄС був активований для українців у березні 2022 року на 1 рік із можливістю продовження до 3 років. Він надає право на проживання, роботу, житло, медичну допомогу та освіту без індивідуальних процедур надання притулку."},
        {"q": "Чи можна подорожувати до іншої країни ЄС, маючи статус тимчасового захисту?", "opts": ["Ні, ви повинні залишатися в країні, яка надала захист", "Так, можна відвідувати до 90 днів, але потрібно повертатися до своєї країни реєстрації", "Так, вільно без будь-яких обмежень", "Лише за наявності дійсного біометричного паспорта"], "ans": 1, "explain": "Ви зареєстровані в одній країні ЄС і маєте там проживати. У Шенгенській зоні можна подорожувати як турист до 90 днів. Щоб постійно переїхати до іншої країни ЄС, потрібно подати заяву на тимчасовий захист там і знятися з реєстрації в першій країні."},
        {"q": "Який документ підтверджує ваш статус тимчасового захисту в країні перебування в ЄС?", "opts": ["Проїзний документ біженця", "Посвідка на проживання або реєстраційне свідоцтво, видані країною перебування", "Картка громадянства ЄС", "Штамп туристичної візи"], "ans": 1, "explain": "Кожна країна ЄС видає різні документи: посвідку на проживання, реєстраційне свідоцтво або спеціальне посвідчення особи. Цей документ підтверджує ваше право на роботу, доступ до послуг та подорожі. Зберігайте його та завчасно поновлюйте до закінчення терміну дії."},
        {"q": "Якщо термін дії вашого дозволу на тимчасовий захист закінчується, що потрібно зробити?", "opts": ["Негайно виїхати з ЄС", "Подати заяву на продовження або інший статус до закінчення терміну дії", "Він поновлюється автоматично — жодних дій не потрібно", "Звертатися лише до посольства України"], "ans": 1, "explain": "Необхідно подати заяву на продовження або інший статус (притулок, національна посвідка) до закінчення терміну. Перебування без дійсного статусу є незаконним і може вплинути на майбутні заяви. Зверніться до місцевого органу з питань імміграції заздалегідь."},
        {"q": "Чи є тимчасовий захист тим самим, що й індивідуальний статус біженця за Женевською конвенцією?", "opts": ["Так, вони ідентичні у всьому", "Ні — тимчасовий захист є швидшим груповим захистом без індивідуальної оцінки", "Ні, статус біженця дає менше прав, ніж тимчасовий захист", "Вони однакові лише в Німеччині"], "ans": 1, "explain": "Тимчасовий захист — це колективний механізм ЄС, набагато швидший від індивідуального надання притулку. Статус біженця за Женевською конвенцією вимагає індивідуального розгляду справи. Ви можете подати заяву на індивідуальний притулок, перебуваючи під тимчасовим захистом."},
        {"q": "Чи можете ви працювати в країні ЄС у рамках тимчасового захисту без окремого дозволу на роботу?", "opts": ["Ні, окремий дозвіл на роботу завжди потрібен", "Так, право на роботу автоматично включено до статусу тимчасового захисту", "Лише в Німеччині та Польщі", "Лише в сільському господарстві та будівництві"], "ans": 1, "explain": "Директива ЄС про тимчасовий захист надає автоматичний доступ до ринку праці — окремий дозвіл на роботу не потрібен. Однак для регульованих професій (медицина, право, інженерія) може знадобитися визнання диплома. Перевірте конкретні правила вашої країни перебування."},
    ],
    "uk_employment_rights": [
        {"q": "Якщо роботодавець відмовляється виплачувати узгоджену зарплату, яким є ваш перший крок?", "opts": ["Погодитися на меншу суму і мовчати", "Подати скаргу до національної інспекції праці — це безкоштовно", "Негайно повернутися в Україну", "Лише адвокати можуть вирішувати спори щодо зарплати"], "ans": 1, "explain": "У кожній країні ЄС є інспекція праці (наприклад, Państwowa Inspekcja Pracy у Польщі, Arbeitsinspektorat в Австрії). Скарги безкоштовні. Ви захищені навіть при неформальній зайнятості. Крадіжка зарплати є незаконною незалежно від національності чи міграційного статусу."},
        {"q": "Чи поширюється національна мінімальна зарплата в країнах ЄС на українських працівників?", "opts": ["Ні, лише на громадян і постійних резидентів", "Так, мінімальна зарплата поширюється на ВСІХ працівників на території країни", "Лише після 6 місяців безперервної роботи", "Лише за наявності офіційного письмового договору"], "ans": 1, "explain": "Рівне ставлення у сфері зайнятості є основним принципом ЄС. Закони про мінімальну зарплату поширюються на всіх працівників незалежно від національності. Будь-який роботодавець, який платить менше, порушує закон і може бути повідомлений до інспекції праці або профспілок."},
        {"q": "Яка максимальна середня тривалість робочого тижня відповідно до законодавства ЄС?", "opts": ["60 годин на тиждень", "48 годин на тиждень включно з понаднормовою роботою в середньому", "40 годин без жодних винятків", "Ліміту робочого часу в ЄС не існує"], "ans": 1, "explain": "Директива ЄС про робочий час встановлює максимум 48 годин на тиждень (в середньому), включно з понаднормовою. Понаднормова робота повинна компенсуватися. Роботодавці не можуть змушувати відмовлятися від цього обмеження — будь-яка відмова повинна бути добровільною і письмовою."},
        {"q": "Чи може роботодавець звільнити вас за повідомлення про порушення охорони праці?", "opts": ["Так, договір може бути розірваний у будь-який час", "Ні, Директива ЄС про захист викривачів забороняє переслідування за такі повідомлення", "Лише якщо ви пропрацювали менше 1 року", "Захистом користуються лише державні службовці"], "ans": 1, "explain": "Директива ЄС про захист викривачів (2019/1937) і національні закони захищають від переслідувань, у тому числі звільнення чи пониження в посаді. У разі звільнення за повідомлення про порушення ви можете вимагати поновлення на роботі або компенсації через суд."},
        {"q": "Чи маєте ви право вступити до профспілки в країні перебування в ЄС?", "opts": ["Ні, до профспілок можуть вступати лише громадяни", "Так, ВСІМ працівникам, включно з іноземцями, надається це право", "Лише після отримання постійного резидентства", "Лише в несекторних галузях економіки"], "ans": 1, "explain": "Свобода об'єднань і право вступати до профспілок гарантовані Хартією основних прав ЄС (стаття 12) для ВСІХ працівників незалежно від національності. Профспілки надають безкоштовну юридичну консультацію, допомагають перевіряти договори та підтримують у трудових спорах."},
        {"q": "Чи маєте ви право на оплачувану щорічну відпустку в країні перебування в ЄС?", "opts": ["Ні, лише постійні резиденти мають оплачувану відпустку", "Так, законодавство ЄС гарантує мінімум 4 тижні оплачуваної відпустки на рік для ВСІХ", "Лише після 2 років роботи в одного роботодавця", "Тривалість відпустки — на розсуд роботодавця"], "ans": 1, "explain": "Директива ЄС про робочий час гарантує мінімум 4 тижні (20 днів) оплачуваної щорічної відпустки для всіх незалежно від національності чи виду договору. Роботодавці не можуть замінити відпустку грошовою компенсацією — ви повинні мати можливість її взяти."},
    ],
    "uk_housing_rights": [
        {"q": "Чи може орендодавець виселити вас негайно без попередження в країнах ЄС?", "opts": ["Так, якщо орендна плата прострочена навіть на 1 день", "Ні, потрібні письмові повідомлення та, як правило, рішення суду", "Так, це стандартна процедура для іноземців", "Лише в приватному житлі, але не в соціальному"], "ans": 1, "explain": "У всіх країнах ЄС виселення вимагає офіційного письмового повідомлення (зазвичай 1–3 місяці) і часто рішення суду. Незаконне виселення (зміна замків, відключення комунальних послуг) є кримінальним злочином. Зверніться до органу з питань житла або безкоштовної правової допомоги при загрозі незаконного виселення."},
        {"q": "Чи поширюються закони про захист орендарів на українських біженців у приватному секторі?", "opts": ["Ні, права орендарів захищають лише громадян", "Так, стандартні права орендарів поширюються на ВСІХ резидентів незалежно від національності", "Лише за договором оренди не менше 1 року", "Лише в субсидованому або соціальному житлі"], "ans": 1, "explain": "Закони про захист орендарів — щодо підвищення орендної плати, процедур виселення, стандартів придатності та правил застави — поширюються на всіх резидентів. Якщо ви підписали договір оренди, ви маєте повні права орендаря. НУО та органи з питань житла можуть безкоштовно роз'яснити місцеві правила."},
        {"q": "Ваш орендодавець вимагає заставу в розмірі 6 місяців орендної плати. Чи це законно?", "opts": ["Так, орендодавці можуть вимагати будь-яку суму", "Залежить від країни — у більшості країн ЄС застава обмежена 1–3 місяцями", "Ніяка застава в ЄС ніколи не є законною", "Правила щодо застави діють лише для договорів понад 1 рік"], "ans": 1, "explain": "Ліміти застави різняться: 2 місяці в Німеччині, 3 місяці у Франції, 5 тижнів в Ірландії. Вимога надмірної застави може бути незаконною. Завжди отримуйте письмову квитанцію та підписаний акт огляду майна. Спори щодо застави можна вирішити в орендному трибуналі."},
        {"q": "Що робити, якщо орендоване житло небезпечне або в дуже поганому стані?", "opts": ["Прийняти це — у вас немає вибору як у біженця", "Повідомити до місцевого органу з питань житла або санітарно-епідеміологічної служби", "Зробити все самостійно за власний рахунок", "Лише орендодавець може вирішувати питання ремонту"], "ans": 1, "explain": "Усе житло повинно відповідати мінімальним стандартам безпеки відповідно до закону. Органи з питань житла можуть провести перевірку та зобов'язати зробити ремонт. Зазвичай вас не можна виселити за повідомлення про небезпечні умови (помста при виселенні незаконна). Документуйте все фотографіями та письмовими скаргами."},
        {"q": "Чи може надзвичайне державне або НУО-житло виселити вас без попередження?", "opts": ["Так, у будь-який час", "Ні, навіть надзвичайне житло вимагає розумного повідомлення та пропозиції альтернатив", "Так, автоматично рівно через 30 днів", "Лише якщо ви порушуєте правила будинку"], "ans": 1, "explain": "Адміністративні процедури регулюють державне та НУО-надане житло. Органи влади зобов'язані надавати розумне повідомлення і не можуть залишити вас без даху. Негайно зверніться до соціальних служб або організацій з допомоги біженцям при загрозі примусового виселення."},
        {"q": "Де можна отримати безкоштовну консультацію з питань житла як українському біженцю в ЄС?", "opts": ["Ніде — потрібно наймати приватного адвоката", "Багато НУО, гарячих ліній та центрів підтримки біженців надають безкоштовні консультації", "Лише у столицях при посольствах", "Лише для сімей з дітьми до 5 років"], "ans": 1, "explain": "Червоний Хрест, Caritas, IRC, місцеві ради у справах біженців та урядові офіси з питань інтеграції надають безкоштовні консультації. Офіційний портал ЄС info4ukraine.eu містить ресурси щодо житла для конкретних країн. Завжди звертайтеся за консультацією перед підписанням договору оренди."},
    ],
    "uk_healthcare_rights": [
        {"q": "Чи мають українці з тимчасовим захистом право на медичну допомогу в країнах ЄС?", "opts": ["Ні, надається лише екстрена допомога", "Так, гарантований доступ до необхідного медичного лікування", "Лише для дітей до 18 років", "Лише за умови оплати повної приватної вартості"], "ans": 1, "explain": "Директива ЄС про тимчасовий захист гарантує доступ до необхідного медичного лікування, а не лише екстреної допомоги. Більшість країн інтегрують українців у свої державні системи охорони здоров'я. Зазвичай потрібно зареєструватися в місцевих органах охорони здоров'я (отримати медичну картку або реєстрацію у лікаря)."},
        {"q": "У разі медичної надзвичайної ситуації в країні перебування, за яким номером телефонувати?", "opts": ["На лінію екстреної допомоги посольства України", "112 — єдиний номер екстреної допомоги ЄС, безкоштовно", "На неекстрену лінію місцевого відділку поліції", "До вашого господаря або орендодавця"], "ans": 1, "explain": "112 — єдиний номер екстреної допомоги в усьому ЄС — безкоштовний. Надання екстреної допомоги НЕ МОЖЕ бути відмовлено нікому незалежно від страховки, статусу проживання чи платоспроможності. Ніколи не відкладайте екстрену допомогу через побоювання щодо вартості або правового статусу."},
        {"q": "Чи мають вагітні українські жінки право на допомогу у зв'язку з вагітністю та пологами в країнах ЄС?", "opts": ["Лише якщо вагітність настала до приїзду до ЄС", "Так, допомога у зв'язку з вагітністю та пологами повністю покрита", "Ні, вагітність не класифікується як невідкладна допомога", "Лише в країнах з двосторонніми угодами з Україною"], "ans": 1, "explain": "Допомога у зв'язку з вагітністю вважається невідкладним медичним лікуванням і покривається Директивою про тимчасовий захист. Це включає дородові огляди, пологи в лікарні та післяпологовий догляд. Зверніться до місцевого органу охорони здоров'я або організації підтримки біженців для реєстрації."},
        {"q": "Чи можете ви отримати підтримку з питань психічного здоров'я як українець у ЄС?", "opts": ["Ні, психічне здоров'я не входить до медичної допомоги для біженців", "Так, психологічна підтримка є частиною гарантованого пакету медичної допомоги", "Лише в спеціалізованих таборах для біженців", "Лише за наявності приватної страховки"], "ans": 1, "explain": "Підтримка з питань психічного здоров'я включена до медичних положень тимчасового захисту. MSF, Médecins du Monde та місцеві НУО пропонують безкоштовне консультування. Багато країн ЄС створили спеціальні гарячі лінії для українців. Підтримка при травмах широко доступна — не соромтесь звертатися."},
        {"q": "Як отримати рецептурні ліки в країні перебування в ЄС?", "opts": ["Неможливо — потрібно привозити всі ліки з України", "Зареєструватися у місцевого лікаря, який може виписати рецепт; скористатися державною системою охорони здоров'я", "Купувати лише за повною приватною ціною", "Рецепти видаються лише в лікарнях, а не в аптеках"], "ans": 1, "explain": "Після реєстрації в місцевій системі охорони здоров'я лікар загальної практики може виписати ліки. За тимчасового захисту ліки, як правило, субсидуються або безкоштовні в рамках державної системи. Привезіть медичні записи або рецепти з України для безперервності лікування."},
        {"q": "Чи можуть діти українців отримати щеплення через державну систему охорони здоров'я країни перебування?", "opts": ["Ні, вони повинні дотримуватися програми щеплень України приватно", "Так, діти можуть отримати доступ до стандартної програми щеплень країни перебування", "Лише після повної офіційної реєстрації як постійних резидентів", "Лише для вакцин, вже отриманих в Україні"], "ans": 1, "explain": "Програми щеплень дітей доступні для всіх дітей, що проживають у країні, включно з тими, хто перебуває під тимчасовим захистом. Школи можуть вимагати записи про щеплення. Місцеві педіатричні клініки можуть надати допомогу з надолуженням щеплень безкоштовно."},
    ],
    "uk_children_education": [
        {"q": "Чи мають українські діти право відвідувати школу в країнах ЄС?", "opts": ["Ні, державна школа лише для громадян і постійних резидентів", "Так, доступ до освіти є правом, гарантованим тимчасовим захистом", "Лише після 6 місяців безперервного проживання", "Лише якщо батьки мають дійсний дозвіл на роботу"], "ans": 1, "explain": "Директива ЄС про тимчасовий захист прямо гарантує дітям доступ до освіти. Більшість країн передбачає зарахування до державних шкіл, мовну підтримку та безкоштовне або субсидоване харчування. Зверніться до місцевої адміністрації або відвідайте info4ukraine.eu для отримання процедур зарахування."},
        {"q": "Якою мовою навчатимуть українських дітей у школах ЄС?", "opts": ["Лише українською", "Офіційною мовою країни перебування, з підтримкою для тих, хто не є рідним носієм", "Англійською як нейтральною мовою для всіх", "Батьки можуть вільно вибирати мову навчання"], "ans": 1, "explain": "Навчання ведеться мовою країни перебування. Більшість країн надає класи мовного занурення, двомовних асистентів або програми надолуження. Багато шкіл також дозволяє продовжувати онлайн-навчання в Україні паралельно з місцевим — двомовний підхід, схвалений органами ЄС та України."},
        {"q": "Чи стягується плата за навчання з дітей українських біженців у державних школах ЄС?", "opts": ["Так, застосовуються ті самі збори для іноземних студентів", "Ні, державне навчання безкоштовне для всіх дітей під тимчасовим захистом", "Оплачуються лише обід та навчальні матеріали за повною ціною", "Варіюється — безкоштовно лише в деяких країнах ЄС"], "ans": 1, "explain": "Державна початкова та середня освіта безкоштовна в усьому ЄС для дітей під тимчасовим захистом. Деякі додаткові витрати (екскурсії, матеріали) можуть застосовуватися, але фонди соціальної підтримки зазвичай їх покривають. Зверніться до школи за допомогою."},
        {"q": "Чи можуть підлітки 16–18 років отримати доступ до старшої школи в країнах ЄС?", "opts": ["Ні, доступ до шкіл для біженців припиняється у 15 років", "Так, право на навчання поширюється до 18 років або кінця обов'язкової освіти", "Доступне лише професійне навчання, а не академічна школа", "Лише в країнах з двосторонніми угодами про освіту з Україною"], "ans": 1, "explain": "Право на навчання поширюється до 18 років для тих, хто перебуває під тимчасовим захистом. Підлітки можуть зараховуватися до гімназій, ліцеїв або профтехучилищ. Доступ до університетів також можливий — перевірте програми Erasmus+ та національні схеми для українських студентів."},
        {"q": "Яка підтримка доступна для українських дітей з особливими освітніми потребами (ООП)?", "opts": ["Жодної — вони повинні справлятися в загальних класах", "Країни перебування зобов'язані вжити розумних коригувань і надати підтримку ООП", "Лише після оцінки, проведеної українською мовою", "Лише у спеціальних школах, ніколи у загальноосвітніх"], "ans": 1, "explain": "Діти з особливими освітніми потребами мають право на розумне пристосування відповідно до директив ЄС про освіту та Конвенції ООН про права дитини. Школи повинні надавати відповідну підтримку та модифіковані навчальні програми. Зверніться до школи з проханням провести офіційну оцінку потреб."},
        {"q": "Чи можуть українські діти продовжувати навчатися в українській онлайн-школі, відвідуючи місцеву школу?", "opts": ["Ні, потрібно вибрати лише одну систему", "Так, подвійне навчання дозволено і заохочується обома сторонами", "Лише у вихідні та поза годинами місцевої школи", "Лише зі спеціальним письмовим дозволом від органів влади"], "ans": 1, "explain": "Уряд України підтримує онлайн-навчання (платформа 'Всеукраїнська школа онлайн') для дітей за кордоном. Більшість країн ЄС дозволяє це паралельно з місцевим навчанням. Це допомагає дітям зберігати мову, культуру та кваліфікацію для можливого повернення в Україну."},
    ],
    "uk_social_benefits": [
        {"q": "Чи мають українці з тимчасовим захистом право на виплати соціальної допомоги в країнах ЄС?", "opts": ["Ні, дозволено лише дохід від роботи", "Так, соціальна допомога гарантована Директивою про тимчасовий захист", "Лише після 2 років безперервного законного проживання", "Лише в разі постійної непрацездатності"], "ans": 1, "explain": "Директива ЄС про тимчасовий захист зобов'язує держави надавати соціальну допомогу, еквівалентну допомозі для власних громадян. Це може включати грошові виплати, підтримку з житла, продовольчі ваучери або інтеграційні надбавки. Зареєструйтесь у місцевих соціальних службах якнайшвидше."},
        {"q": "Чи можуть діти українських біженців отримувати виплати на дитину в країнах ЄС?", "opts": ["Ні, лише громадяни і постійні резиденти отримують таку допомогу", "Так, допомога на дитину, як правило, доступна для дітей під тимчасовим захистом", "Лише якщо обидва батьки працюють повний робочий день", "Лише для дітей до 5 років"], "ans": 1, "explain": "Більшість країн ЄС поширює допомогу на дитину на українських дітей. Наприклад: Німеччина виплачує Kindergeld, Франція — Allocations Familiales, Ірландія — Child Benefit. Зареєструйтеся у місцевому відділі сімейних виплат незабаром після приїзду."},
        {"q": "Якщо ви втрачаєте роботу в країні перебування, чи можна отримати допомогу по безробіттю?", "opts": ["Ні, допомогу можуть отримувати лише громадяни", "Так, якщо ви робили внески до системи соціального страхування під час законної роботи", "Потрібно виїхати і повернутися в Україну", "Лише після мінімального 3-річного стажу внесків"], "ans": 1, "explain": "Допомога по безробіттю пов'язана з внесками до соціального страхування під час законної роботи. Кваліфікаційний період (зазвичай 6–12 місяців внесків) і розмір виплат варіюються залежно від країни. Негайно зареєструйтеся в національній службі зайнятості."},
        {"q": "Чи існують спеціальні програми фінансової підтримки для покриття витрат на інтеграцію українців?", "opts": ["Ні, існує лише звичайна система соціального захисту", "Так, у багатьох країнах є спеціальні фонди, гранти на курси мови та стартові надбавки", "Лише для сімей з трьома і більше дітьми", "Лише протягом першого місяця після приїзду"], "ans": 1, "explain": "Багато країн ЄС створили спеціальні програми для українців: Bürgergeld у Німеччині, пільги PESEL у Польщі, інтеграційні надбавки в Чехії, Community Recognition Fund в Ірландії. НУО також надають екстрену грошову допомогу. Ознайомтесь із програмами вашої конкретної країни."},
        {"q": "Чи потрібно сплачувати прибутковий податок, якщо ви працюєте в країні ЄС?", "opts": ["Ні, біженці повністю звільнені від оподаткування", "Так, якщо дохід перевищує неоподатковуваний мінімум — потрібно платити", "Лише роботодавці сплачують податки; працівники нічого не винні", "Обов'язки виникають лише після постійного резидентства"], "ans": 1, "explain": "Усі працівники, включно з тими під тимчасовим захистом, повинні сплачувати прибутковий податок понад неоподатковуваний мінімум. Податок зазвичай утримується роботодавцем. Подача річної декларації може призвести до повернення переплати. Безкоштовна податкова консультація доступна через соціальні служби та НУО."},
        {"q": "Який офіційний портал ЄС для українців про права та послуги в країнах перебування?", "opts": ["ukrainehelp.gov.ua", "info4ukraine.eu — офіційний портал Єврокомісії", "europarl.europa.eu/ukraine", "unhcr.org/ukraine-crisis"], "ans": 1, "explain": "info4ukraine.eu підтримується Єврокомісією та надає практичну інформацію для конкретних країн про реєстрацію тимчасового захисту, житло, роботу, медичну допомогу, освіту та соціальну підтримку всіма мовами ЄС, включно з українською."},
    ],
    "uk_border_rights": [
        {"q": "Чи можуть громадяни України з біометричним паспортом в'їжджати до ЄС без візи?", "opts": ["Ні, Шенгенська віза завжди потрібна", "Так, безвізовий в'їзд на строк до 90 днів у будь-який 180-денний період", "Лише через конкретні визначені прикордонні переходи", "Лише за попередньої реєстрації як біженця"], "ans": 1, "explain": "З 2017 року громадяни України з біометричними паспортами можуть в'їжджати до Шенгенської зони без візи на строк до 90 днів у будь-який 180-денний період. Для тих, хто тікає від конфлікту, Директива про тимчасовий захист додатково усуває бар'єри."},
        {"q": "Якщо у вас немає біометричного паспорта, чи можна в'їхати до ЄС для отримання захисту?", "opts": ["Ні, дійсний паспорт є обов'язковим для в'їзду", "Так, особам, які рятуються від переслідувань, не може бути відмовлено у захисті незалежно від документів", "Лише в аеропортах зі спеціальними стійками для біженців", "Лише за наявності іменного спонсора в країні ЄС"], "ans": 1, "explain": "Люди, які рятуються від переслідувань, мають право шукати притулок незалежно від наявності документів відповідно до міжнародного права. Прикордонники не можуть відмовити вам лише через відсутність документів. Українське посвідчення особи широко приймалося на кордонах ЄС. Чітко повідомте офіцерів про звернення по захист."},
        {"q": "Чи можуть прикордонники ЄС затримати вас при зверненні за захистом на кордоні?", "opts": ["Так, безстроково до повного вирішення справи", "Лише як крайній захід і на мінімально необхідний термін під судовим наглядом", "Так, стандартно на строк до 6 місяців", "Ні, ви повинні бути негайно і безумовно допущені"], "ans": 1, "explain": "Затримання шукачів притулку повинно відповідати Директиві ЄС про умови прийому — це крайній захід, обмежений у часі та підлягає судовому перегляду. У разі затримання ви маєте право на адвоката, перекладача та зв'язок із УВКБ ООН та НУО."},
        {"q": "Що робити, якщо прикордонники поводяться жорстоко або відмовляють у доступі до процедур притулку?", "opts": ["Змиритись і спробувати в'їхати з іншої країни", "Задокументувати все і повідомити до УВКБ ООН, Механізму скарг Frontex або омбудсмена", "Повідомляти лише уряду України — більше ніхто не може допомогти", "Юридично ви нічого не можете зробити"], "ans": 1, "explain": "Відштовхування (примусове повернення без розгляду) та насильство на кордоні порушують законодавство ЄС та міжнародне право. Frontex має Офіцера з основних прав і публічний механізм скарг. Задокументуйте інцидент і негайно зверніться до НУО."},
        {"q": "Після в'їзду до країни ЄС в який строк потрібно зареєструватися для тимчасового захисту?", "opts": ["Потрібно зареєструватися на кордоні до в'їзду", "Якнайшвидше — зазвичай протягом днів або тижнів, як вказують місцеві органи", "Протягом 1 року — жодної терміновості немає", "Лише коли ви вирішите почати працювати"], "ans": 1, "explain": "Зареєструйтесь якнайшвидше після приїзду. Реєстрація надає правовий статус, доступ до житла, медичної допомоги та соціальної підтримки. Затримки можуть ускладнити доступ до пільг. Перевірте info4ukraine.eu для конкретних процедур вашої країни."},
        {"q": "Чи можуть прикордонники ЄС конфіскувати ваш мобільний телефон без правового обґрунтування?", "opts": ["Так, вони мають необмежені повноваження щодо вилучення телефонів", "Лише на підставі конкретного правового повноваження з документально підтвердженими причинами", "Так, для перевірки злочинних зв'язків — це стандартна процедура", "Ні, телефони ніколи не перевіряються на внутрішніх кордонах ЄС"], "ans": 1, "explain": "Вилучення телефонів без правового обґрунтування порушує право на приватність відповідно до Хартії основних прав ЄС. Масові перевірки телефонів шукачів притулку без індивідуального обґрунтування були визнані судами ЄС непропорційними. Оскаржте будь-яке невиправдане вилучення через безкоштовну правову допомогу."},
    ],
}

LANGUAGES = ["hi", "bn", "ta", "te", "kn", "sat"]

DB_PATH = os.path.join(os.path.dirname(__file__), "quiz_translations.db")


def init_db():
    """Create the quiz tables if they don't exist."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS quiz_questions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            topic TEXT NOT NULL,
            language TEXT NOT NULL,
            question_index INTEGER NOT NULL,
            question TEXT NOT NULL,
            options TEXT NOT NULL,
            answer_index INTEGER NOT NULL,
            explanation TEXT NOT NULL,
            UNIQUE(topic, language, question_index)
        )
    """)
    conn.commit()
    conn.close()


def is_topic_translated(topic: str, language: str) -> bool:
    """Check if a topic already has translations for a language."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM quiz_questions WHERE topic=? AND language=?", (topic, language))
    count = c.fetchone()[0]
    conn.close()
    return count > 0


def save_translations(topic: str, language: str, questions: list[dict]):
    """Save translated questions to SQLite."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    # Delete existing translations for this topic/language
    c.execute("DELETE FROM quiz_questions WHERE topic=? AND language=?", (topic, language))
    for i, q in enumerate(questions):
        c.execute(
            "INSERT INTO quiz_questions (topic, language, question_index, question, options, answer_index, explanation) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (topic, language, i, q["q"], json.dumps(q["opts"], ensure_ascii=False), q["ans"], q["explain"])
        )
    conn.commit()
    conn.close()


def save_english_questions():
    """Save original English questions to DB."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    for topic, questions in QUIZ_BANK.items():
        c.execute("DELETE FROM quiz_questions WHERE topic=? AND language='en'", (topic,))
        for i, q in enumerate(questions):
            c.execute(
                "INSERT INTO quiz_questions (topic, language, question_index, question, options, answer_index, explanation) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (topic, "en", i, q["q"], json.dumps(q["opts"], ensure_ascii=False), q["ans"], q["explain"])
            )
    conn.commit()
    conn.close()
    print(f"[OK] Saved {sum(len(qs) for qs in QUIZ_BANK.values())} English questions across {len(QUIZ_BANK)} topics")


def save_ukrainian_questions():
    """Save Ukrainian-specific questions (EU host-country rights) directly under 'uk' language."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    for topic, questions in UKRAINIAN_QUIZ_BANK.items():
        c.execute("DELETE FROM quiz_questions WHERE topic=? AND language='uk'", (topic,))
        for i, q in enumerate(questions):
            c.execute(
                "INSERT INTO quiz_questions (topic, language, question_index, question, options, answer_index, explanation) "
                "VALUES (?, ?, ?, ?, ?, ?, ?)",
                (topic, "uk", i, q["q"], json.dumps(q["opts"], ensure_ascii=False), q["ans"], q["explain"])
            )
    conn.commit()
    conn.close()
    print(f"[OK] Saved {sum(len(qs) for qs in UKRAINIAN_QUIZ_BANK.values())} Ukrainian questions "
          f"across {len(UKRAINIAN_QUIZ_BANK)} topics (EU host-country rights)")


def _extract_json_array(text: str) -> list:
    """Parse JSON array from model response."""
    text = text.strip()
    if text.startswith("```"):
        text = text.split("\n", 1)[-1].rsplit("```", 1)[0].strip()
    if text.startswith("["):
        return json.loads(text)
    start = text.find("[")
    end = text.rfind("]") + 1
    if start >= 0 and end > start:
        return json.loads(text[start:end])
    raise ValueError("No JSON array found in response")


async def translate_topic(topic: str, questions: list[dict], language: str) -> list[dict]:
    """Translate one topic's questions to one language using Gemma."""
    lang_name = LANGUAGE_NAMES.get(language, language)

    batch = [
        {"id": i, "q": q["q"], "opts": q["opts"], "explain": q["explain"]}
        for i, q in enumerate(questions)
    ]

    prompt = (
        f"Translate the following quiz questions, their answer options, and explanations "
        f"from English to {lang_name}.\n\n"
        f"CRITICAL RULES:\n"
        f"- Translate EVERYTHING: questions, option text, and explanations.\n"
        f"- Keep the JSON structure EXACTLY the same.\n"
        f"- Do NOT translate Article numbers, Act names within the explanation (keep them in English within the translated sentence).\n"
        f"- Output ONLY valid JSON — no markdown, no code fences, no commentary.\n\n"
        f"Input JSON:\n{json.dumps(batch, ensure_ascii=False)}\n\n"
        f"Output the translated JSON array:"
    )

    result = await gemma_service.generate_text(
        prompt, language=language,
        system_instruction="You are a translator. Output ONLY valid JSON. No markdown, no code blocks, no extra text."
    )

    translated = _extract_json_array(result)

    out = []
    for i, orig in enumerate(questions):
        t = translated[i] if i < len(translated) else {}
        out.append({
            "q": t.get("q", orig["q"]),
            "opts": t.get("opts", orig["opts"]),
            "ans": orig["ans"],  # Always keep original answer index
            "explain": t.get("explain", orig["explain"]),
        })

    return out


async def main():
    print("=" * 60)
    print("DHARMA-NYAYA Quiz Translation Pipeline")
    print("=" * 60)

    settings = get_settings()
    if not settings.GEMINI_API_KEY:
        print("[ERROR] GEMINI_API_KEY not set. Check your .env file.")
        return

    init_db()

    # Step 1: Save English originals
    save_english_questions()

    # Step 2: Save Ukrainian-specific questions (EU host-country rights)
    save_ukrainian_questions()

    # Step 3: Translate Indian topics to other languages (Ukrainian handled separately above)
    total_topics = len(QUIZ_BANK)
    total_langs = len(LANGUAGES)
    total_jobs = total_topics * total_langs
    done = 0

    for lang in LANGUAGES:
        lang_name = LANGUAGE_NAMES.get(lang, lang)
        print(f"\n── Translating to {lang_name} ({lang}) ──")

        for topic, questions in QUIZ_BANK.items():
            done += 1
            # Check if already translated
            if is_topic_translated(topic, lang):
                print(f"  [{done}/{total_jobs}] {topic} — already translated, skipping")
                continue

            print(f"  [{done}/{total_jobs}] {topic} ({len(questions)} questions)...", end=" ", flush=True)
            try:
                translated = await translate_topic(topic, questions, lang)
                save_translations(topic, lang, translated)
                print("OK")
            except Exception as e:
                print(f"FAILED: {e}")
                # Save English as fallback
                save_translations(topic, lang, questions)
                print(f"         → saved English fallback")

    # Summary
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM quiz_questions")
    total = c.fetchone()[0]
    c.execute("SELECT DISTINCT language FROM quiz_questions")
    langs = [r[0] for r in c.fetchall()]
    conn.close()

    print(f"\n{'=' * 60}")
    print(f"DONE! {total} questions stored in {DB_PATH}")
    print(f"Languages: {', '.join(sorted(langs))}")
    print(f"{'=' * 60}")


if __name__ == "__main__":
    asyncio.run(main())
