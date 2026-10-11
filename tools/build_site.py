#!/usr/bin/env python3
"""Render complete English/French GitHub Pages documents using only the standard library."""
import html
import json
import re
from pathlib import Path
from datetime import date

ROOT = Path(__file__).resolve().parents[1]
BASE = 'https://halhoulmhamed-droid.github.io'
NAME = 'Halhoul Mhamed'
PAGES = json.loads((ROOT / 'content/pages.json').read_text())
LABELS = {
 'en': {'home':'Home','about':'About','projects':'Projects','contact':'Contact','skip':'Skip to content','nav':'Main navigation','languages':'Language','menu':'Menu','footer':'Mathematical modelling · Scientific computing','academic':'Master’s scientific project','software':'Software project','read':'Read the study','repo':'Repository','all':'All projects','onpage':'On this page','evidence':'Methods, evidence & limitations','source':'Documented academic work, not peer-reviewed scientific publications.','research':'Research interests','synthesis':'Comparative synthesis','status':'M2 in progress'},
 'fr': {'home':'Accueil','about':'Parcours','projects':'Projets','contact':'Contact','skip':'Aller au contenu','nav':'Navigation principale','languages':'Langue','menu':'Menu','footer':'Modélisation mathématique · Calcul scientifique','academic':'Projet scientifique de Master','software':'Projet logiciel','read':'Lire l’étude','repo':'Dépôt','all':'Tous les projets','onpage':'Sur cette page','evidence':'Méthodes, résultats et limites','source':'Travaux universitaires documentés, distincts des publications scientifiques évaluées par les pairs.','research':'Axes d’intérêt','synthesis':'Synthèse comparative','status':'M2 en cours'}
}

def esc(value): return html.escape(str(value), quote=True)
def path(route, lang): return ('/fr' if lang == 'fr' else '') + route

def link(url, label, cls=''):
    external = url.startswith('https://')
    return f'<a href="{esc(url)}"' + (f' class="{esc(cls)}"' if cls else '') + (' rel="noopener noreferrer"' if external else '') + f'>{label}</a>'

def document(route, lang, title, description, body, category='home', noindex=False):
    l = LABELS[lang]; url = BASE + path(route, lang)
    navigation=''.join(link(path(r,lang),l[k]) if k!=category else f'<a href="{path(r,lang)}" aria-current="page">{l[k]}</a>' for k,r in [('home','/'),('about','/about/'),('projects','/projects/'),('contact','/contact/')])
    languages=''.join(f'<a class="lang-link" href="{path(route,code)}" lang="{code}" hreflang="{code}" data-language-link' + (' aria-current="true"' if code==lang else '') + f' aria-label="{label}">{code.upper()}</a>' for code,label in [('en','English'),('fr','Français')])
    alternates=''.join(f'<link rel="alternate" hreflang="{code}" href="{BASE + path(route,code)}">' for code in ['en','fr']) + f'<link rel="alternate" hreflang="x-default" href="{BASE+route}">'
    schema = {'@context':'https://schema.org','@type':'WebPage','name':title,'url':url,'inLanguage':lang,'description':description,'about':{'@type':'Person','name':NAME,'url':BASE+'/','email':'halhoul.mhamed@etu.uae.ac.ma','affiliation':{'@type':'CollegeOrUniversity','name':'Université Abdelmalek Essaâdi — Faculté Polydisciplinaire de Larache'}}}
    rendered = f'''<!doctype html>
<html lang="{lang}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(title)} — {NAME}</title>
<meta name="description" content="{esc(description)}">
<meta name="author" content="{NAME}">
<meta name="robots" content="{'noindex, follow' if noindex else 'index, follow'}">
<meta name="theme-color" content="#f5f3ed">
<link rel="canonical" href="{url}">
{alternates}
<link rel="icon" href="/assets/favicon.svg" type="image/svg+xml">
<script>document.documentElement.classList.add("js");</script>
<link rel="stylesheet" href="/assets/css/styles.css">
<meta property="og:type" content="website">
<meta property="og:site_name" content="{NAME} — Academic portfolio">
<meta property="og:title" content="{esc(title)} — {NAME}">
<meta property="og:description" content="{esc(description)}">
<meta property="og:url" content="{url}">
<meta property="og:locale" content="{'fr_FR' if lang=='fr' else 'en_GB'}">
<meta property="og:locale:alternate" content="{'en_GB' if lang=='fr' else 'fr_FR'}">
<meta name="twitter:card" content="summary">
<meta name="twitter:title" content="{esc(title)} — {NAME}">
<meta name="twitter:description" content="{esc(description)}">
<script type="application/ld+json">{json.dumps(schema,ensure_ascii=False).replace('<','\\u003c')}</script>
<script src="/assets/js/main.js" defer></script>
</head>
<body>
<a class="skip-link" href="#main-content">{l['skip']}</a>
<header class="site-header" data-site-header><div class="shell header-inner">
<a class="brand" href="{path('/',lang)}"><span class="brand-mark" aria-hidden="true">HM</span><span class="brand-name">{NAME}</span></a>
<button class="nav-toggle" type="button" aria-controls="site-nav" aria-expanded="false" data-nav-toggle>{l['menu']} <span class="nav-toggle-mark" aria-hidden="true"></span></button>
<nav class="site-nav" id="site-nav" aria-label="{l['nav']}" data-site-nav>{navigation}</nav>
<nav class="language-switch" aria-label="{l['languages']}">{languages}</nav>
</div></header>
<main id="main-content" tabindex="-1">{body}</main>
<footer class="site-footer"><div class="shell footer-inner"><div><p>© <span data-year>2026</span> {NAME}</p><p class="muted">{l['footer']}</p></div><div class="footer-links">{link(path('/contact/',lang),l['contact'])}{link('https://github.com/halhoulmhamed-droid','GitHub')}{link('https://orcid.org/0009-0007-3893-2603','ORCID')}</div></div></footer>
</body></html>
'''
    arrow = '<svg class="inline-icon" aria-hidden="true" viewBox="0 0 16 16" width="16" height="16"><path d="M3 13 13 3M3 3h10v10"/></svg>'
    back = '<svg class="inline-icon" aria-hidden="true" viewBox="0 0 16 16" width="16" height="16"><path d="M14 8H2m5-5L2 8l5 5"/></svg>'
    return rendered.replace('↗', arrow).replace('←', back)

def card(key,lang,index):
    p=PAGES[key];l=LABELS[lang]
    tags=''.join(f'<span class="tag">{esc(t)}</span>' for t in p.get('tags_'+lang,[]))
    kind=l['software'] if key in ['hujja','talk'] else l['synthesis'] if key=='synthesis' else l['academic']
    return f'<article class="project-card"><span class="project-number">{index:02d}</span><p class="project-kind">{kind}</p><h3>{link(path(p["route"],lang),esc(p["title_"+lang]))}</h3><p>{p["summary_"+lang]}</p><div class="tags">{tags}</div><div class="project-links">{link(path(p["route"],lang),l["read"]+" <span aria-hidden=\"true\">↗</span>")}</div></article>'

def contacts(lang,compact=False):
    if lang=='fr':
        title='Échangeons autour d’une question scientifique.';desc='Pour un échange avec un encadrant de doctorat, un laboratoire ou un partenaire scientifique, vous pouvez me contacter directement.';a='Adresse universitaire';b='Adresse personnelle'
    else:
        title='Let’s start with a scientific question.';desc='For conversations with prospective doctoral supervisors, laboratories and scientific partners, please contact me directly.';a='University email';b='Personal email'
    return f'<section class="section shell" id="contact"><div class="section-heading"><div><p class="eyebrow">{LABELS[lang]["contact"]}</p><h2>{title}</h2></div><p class="section-intro">{desc}</p></div><div class="contact-grid"><article class="contact-card"><p class="project-kind">{a}</p>{link("mailto:halhoul.mhamed@etu.uae.ac.ma","halhoul.mhamed@etu.uae.ac.ma")}</article><article class="contact-card"><p class="project-kind">{b}</p>{link("mailto:halhoulmhamed@gmail.com","halhoulmhamed@gmail.com")}</article></div></section>'

def home(lang):
    l=LABELS[lang]
    if lang=='fr':
        headline='Des modèles mathématiques.<br><em>Des résultats vérifiables.</em>'
        intro='Étudiant en M2, je développe un parcours en modélisation mathématique, optimisation et calcul scientifique, avec un intérêt pour les problèmes inverses et l’apprentissage.'
        focus='Du modèle à la reconstruction'; focusintro='Trois projets scientifiques de Master : restaurer une image, étudier l’optimisation neuronale et reconstruire une source à partir de mesures indirectes.'
        fields=[('Formation','M2 en cours'),('Établissement','Faculté Polydisciplinaire de Larache'),('Université','Université Abdelmalek Essaâdi')]
        studyhead='Une démarche scientifique, explicitée.';studydesc='Problème, protocole, résultats et limites : chaque étude renvoie à ses sources et à ses artefacts publics.'
        band='Master « Modélisation mathématique et applications et apprentissages »'; bandtext='Université Abdelmalek Essaâdi · Faculté Polydisciplinaire de Larache'
        synhead='Lire les études inverses ensemble.';syntxt='Une synthèse de trois études examine ce que les critères établissent, ce qui reste inconclusif et les limites du transfert d’un scénario à l’autre.'
        softhead='Des outils, avec un périmètre précis.';softdesc='Deux projets logiciels complémentaires, présentés dans leur état publié : démonstrateur local et contrats en pré-alpha.'
    else:
        headline='Mathematical models.<br><em>Verifiable evidence.</em>'
        intro='An M2 student developing a path in mathematical modelling, optimization and scientific computing, with interests in inverse problems and learning.'
        focus='From model to reconstruction';focusintro='Three Master’s scientific projects: restoring an image, studying neural optimization and reconstructing a source from indirect measurements.'
        fields=[('Programme stage','M2 in progress'),('Faculty','Faculté Polydisciplinaire de Larache'),('University','Université Abdelmalek Essaâdi')]
        studyhead='A scientific process, made explicit.';studydesc='Problem, protocol, results and limitations: each study connects to public sources and research artefacts.'
        band='Master « Modélisation mathématique et applications et apprentissages »';bandtext='Université Abdelmalek Essaâdi · Faculté Polydisciplinaire de Larache'
        synhead='Read the inverse studies together.';syntxt='A synthesis of three studies examines what the criteria establish, what remains inconclusive and the limits of transferring a finding across scenarios.'
        softhead='Software with a defined scope.';softdesc='Two complementary software projects, presented in their published state: a local demo and pre-alpha contracts.'
    facts=''.join(f'<div><dt>{a}</dt><dd>{b}</dd></div>' for a,b in fields)
    return f'''<section class="hero shell"><div class="hero-grid"><div><p class="eyebrow">{NAME} <span aria-hidden="true">/</span> {l['status']}</p><h1>{headline}</h1><p class="lead">{intro}</p><div class="project-links">{link(path('/projects/',lang),l['projects'],'button button-primary')}{link(path('/about/',lang),l['about'],'button button-secondary')}</div></div><div class="hero-aside"><p class="eyebrow">{l['research']}</p><h2>{focus}</h2><p>{focusintro}</p><dl class="fact-list">{facts}</dl></div></div></section>
<div class="identity-band"><div class="shell"><div><p class="eyebrow">{l['status']}</p><h2 lang="fr">{band}</h2><p>{bandtext}</p></div>{link(path('/contact/',lang),l['contact']+' ↗','button button-secondary')}</div></div>
<section class="section shell"><div class="section-heading"><div><p class="eyebrow">01 / {l['academic']}</p><h2>{studyhead}</h2></div><p class="section-intro">{studydesc}</p></div><div class="project-grid">{''.join(card(k,lang,i+1) for i,k in enumerate(['pde','nn','inverse']))}</div><p class="note">{l['source']}</p></section>
<section class="section shell split-section"><div><p class="section-label">02 / {l['synthesis']}</p><h2>{synhead}</h2></div><div class="split-content"><p class="lead">{syntxt}</p>{link(path(PAGES['synthesis']['route'],lang),l['read']+' ↗','text-link')}</div></section>
<section class="section shell"><div class="section-heading"><div><p class="eyebrow">03 / {l['software']}</p><h2>{softhead}</h2></div><p class="section-intro">{softdesc}</p></div><div class="project-grid software-grid">{card('talk',lang,1)}{card('hujja',lang,2)}</div></section>{contacts(lang)}'''

def projects(lang):
    l=LABELS[lang]
    title='Études, méthodes et logiciels.' if lang=='fr' else 'Studies, methods and software.'
    intro='Une sélection de travaux universitaires et de projets logiciels, accompagnés de résultats, de limites et de sources vérifiables.' if lang=='fr' else 'Selected academic work and software projects, with results, limitations and verifiable sources.'
    syn='Trois études inverses : synthèse' if lang=='fr' else 'Three inverse studies: synthesis'
    return f'<section class="page-intro shell"><p class="eyebrow">{l["projects"]}</p><h1>{title}</h1><p class="lead">{intro}</p></section><section class="section shell"><div class="section-heading"><div><p class="eyebrow">01</p><h2>{l["academic"]}</h2></div><p class="section-intro">{l["source"]}</p></div><div class="project-grid">'+''.join(card(k,lang,i+1) for i,k in enumerate(['pde','nn','inverse']))+f'</div></section><section class="section shell"><div class="section-heading"><div><p class="eyebrow">02</p><h2>{syn}</h2></div></div><div class="project-grid synthesis-grid">{card("synthesis",lang,4)}</div></section><section class="section shell"><div class="section-heading"><div><p class="eyebrow">03</p><h2>{l["software"]}</h2></div></div><div class="project-grid software-grid">{card("talk",lang,1)}{card("hujja",lang,2)}</div></section>'

def case(key,lang):
    p=PAGES[key]; l=LABELS[lang];content=p['body_'+lang]
    headings=re.findall(r'<h2 id="([^"]+)">(.*?)</h2>',content)
    toc=''.join(link('#'+id_,re.sub('<[^>]*>','',label)) for id_,label in headings)
    kind=l['software'] if key in ['hujja','talk'] else l['synthesis'] if key=='synthesis' else l['academic']
    attribution=p.get('attribution_'+lang,'')
    return f'<article><header class="case-hero shell"><p class="breadcrumb">{link(path("/projects/",lang),"← "+l["all"])}</p><p class="eyebrow">{kind}</p><h1>{esc(p["title_"+lang])}</h1><p class="lead">{p["description_"+lang]}</p><div class="case-meta">{attribution}</div></header><div class="case-layout shell"><nav class="case-nav" aria-label="{l["onpage"]}"><p class="eyebrow">{l["onpage"]}</p>{toc}</nav><div class="case-body prose">{content}</div></div></article>'

def about(lang):
    if lang=='fr':
        title='Un parcours en mathématiques appliquées.';intro='Je suis Halhoul Mhamed, étudiant en deuxième année de Master (M2), à la Faculté Polydisciplinaire de Larache de l’Université Abdelmalek Essaâdi.'
        training='Formation';stage='M1 terminé · M2 en cours';official='Master « Modélisation mathématique et applications et apprentissages »';degree='Licence d’Études Fondamentales — Sciences Mathématiques et Applications';university='Université Ibn Zohr · 2015'
        details='Le titre officiel du Master est conservé en français. Le diplôme est en cours de préparation.'
        fields=[('Modélisation','Formuler les hypothèses, les variables et les relations d’un modèle.'),('Optimisation','Étudier des méthodes et leur comportement dans des protocoles définis.'),('Calcul scientifique','Relier l’analyse numérique à des implémentations et à des résultats reproductibles.'),('Apprentissage','Examiner le rôle des modèles appris dans un cadre mathématique et expérimental.')]
        interests='Axes d’intérêt';teaching='Enseignement des mathématiques';teachtext='Enseignement des mathématiques dans le secondaire marocain depuis 2016. Une période distincte de cours particuliers est documentée entre 2009 et 2011.'
        trajectory='Vers la recherche doctorale';trajectorytext='Je souhaite approfondir les liens entre modélisation, problèmes inverses, optimisation et apprentissage. Les projets présentés ici documentent un travail de Master ; ils ne constituent pas une revendication de nouveauté algorithmique ou de publication scientifique.'
        course='Socle de formation';coursetext='Le parcours de M1 comprend notamment l’analyse numérique et matricielle, l’analyse fonctionnelle, les méthodes numériques pour les EDP, l’optimisation, les probabilités et les statistiques. En M2, les projets présentés portent sur la modélisation déterministe, l’optimisation et les problèmes inverses.'
    else:
        title='A path through applied mathematics.';intro='I am Halhoul Mhamed, a second-year Master’s student (M2) at Faculté Polydisciplinaire de Larache, Université Abdelmalek Essaâdi.'
        training='Education';stage='M1 completed · M2 in progress';official='Master « Modélisation mathématique et applications et apprentissages »';degree='Licence d’Études Fondamentales — Sciences Mathématiques et Applications';university='Université Ibn Zohr · 2015'
        details='The official French Master’s programme title is retained. The degree is in progress.'
        fields=[('Modelling','Formulating assumptions, variables and relationships in a mathematical model.'),('Optimization','Studying methods and their behaviour within defined protocols.'),('Scientific computing','Connecting numerical analysis to implementations and reproducible evidence.'),('Learning','Examining the role of learned models in a mathematical and experimental framework.')]
        interests='Research interests';teaching='Mathematics teaching';teachtext='Mathematics teaching in Moroccan secondary schools began in 2016. A separate period of private mathematics tutoring is documented for 2009–2011.'
        trajectory='Towards doctoral research';trajectorytext='I aim to deepen the connections between modelling, inverse problems, optimization and learning. The projects here document Master’s work; they do not claim algorithmic novelty or scientific publication.'
        course='Mathematical foundation';coursetext='M1 study includes numerical and matrix analysis, functional analysis, numerical methods for PDEs, optimization, probability and statistics. The M2 projects presented here concern deterministic modelling, optimization and inverse problems.'
    fieldhtml=''.join(f'<article class="fact"><h3>{a}</h3><p>{b}</p></article>' for a,b in fields)
    return f'<section class="page-intro shell"><p class="eyebrow">{LABELS[lang]["about"]}</p><h1>{title}</h1><p class="lead">{intro}</p></section><section class="section shell split-section"><p class="section-label">01 / {training}</p><div class="split-content"><ol class="record-list"><li><p class="project-kind">{stage}</p><h2 lang="fr">{official}</h2><p>Université Abdelmalek Essaâdi · Faculté Polydisciplinaire de Larache</p><p>{details}</p></li><li><p class="project-kind">{university}</p><h3 lang="fr">{degree}</h3></li></ol><h3>{course}</h3><p>{coursetext}</p></div></section><section class="section shell"><div class="section-heading"><div><p class="eyebrow">02</p><h2>{interests}</h2></div></div><div class="fact-grid">{fieldhtml}</div></section><section class="section shell split-section"><p class="section-label">03 / {teaching}</p><div class="split-content"><h2>{teaching}</h2><p>{teachtext}</p></div></section><section class="section shell split-section"><p class="section-label">04</p><div class="split-content"><h2>{trajectory}</h2><p class="lead">{trajectorytext}</p>{link(path("/projects/",lang),LABELS[lang]["projects"]+" ↗","text-link")}</div></section>{contacts(lang)}'

def write(route,lang,title,description,body,category='home',noindex=False):
    location = path(route,lang).lstrip('/')
    dest = ROOT / (location if route.endswith('.html') else location+'index.html')
    dest.parent.mkdir(parents=True,exist_ok=True)
    dest.write_text(document(route,lang,title,description,body,category,noindex))

routes=['/','/about/','/projects/','/contact/']+[p['route'] for p in PAGES.values()]
for lang in ['en','fr']:
    write('/',lang,'Portfolio académique' if lang=='fr' else 'Academic portfolio','Halhoul Mhamed — M2 en cours à l’Université Abdelmalek Essaâdi. Modélisation, optimisation, problèmes inverses et calcul scientifique.' if lang=='fr' else 'Halhoul Mhamed — M2 student at Université Abdelmalek Essaâdi. Mathematical modelling, optimization, inverse problems and scientific computing.',home(lang))
    write('/about/',lang,'Parcours' if lang=='fr' else 'About','Formation, intérêts scientifiques et parcours de Halhoul Mhamed, étudiant en M2 à la Faculté Polydisciplinaire de Larache.' if lang=='fr' else 'Education, scientific interests and background of Halhoul Mhamed, an M2 student at Faculté Polydisciplinaire de Larache.',about(lang),'about')
    write('/projects/',lang,'Projets' if lang=='fr' else 'Projects','Projets scientifiques de Master et projets logiciels : protocoles, résultats, limites et sources publiques.' if lang=='fr' else 'Master’s scientific projects and software work: protocols, results, limitations and public sources.',projects(lang),'projects')
    write('/contact/',lang,'Contact et échanges scientifiques' if lang=='fr' else 'Contact & research conversations','Contacter Halhoul Mhamed pour un échange scientifique ou doctoral.' if lang=='fr' else 'Contact Halhoul Mhamed for scientific and doctoral research conversations.',contacts(lang).replace('<h2>', '<h1>', 1).replace('</h2>', '</h1>', 1),'contact')
    for key,p in PAGES.items(): write(p['route'],lang,p['title_'+lang],p['description_'+lang],case(key,lang),'projects')
    title='Page introuvable' if lang=='fr' else 'Page not found'
    text='Cette adresse ne correspond à aucune page. Retrouvez les études et les coordonnées depuis la navigation.' if lang=='fr' else 'This address does not match a page. Find the studies and contact details through the navigation.'
    write('/404.html',lang,title,text,f'<section class="page-intro shell"><p class="eyebrow">404</p><h1>{title}</h1><p class="lead">{text}</p>{link(path("/",lang),LABELS[lang]["home"],"button button-primary")}</section>',noindex=True)
urls=[]
for route in routes:
    for lang in ['en','fr']:
        alternates=''.join(f'<xhtml:link rel="alternate" hreflang="{code}" href="{BASE+path(route,code)}"/>' for code in ['en','fr'])+f'<xhtml:link rel="alternate" hreflang="x-default" href="{BASE+route}"/>'
        urls.append(f'<url><loc>{BASE+path(route,lang)}</loc><lastmod>2026-10-11</lastmod>{alternates}</url>')
(ROOT/'sitemap.xml').write_text('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:xhtml="http://www.w3.org/1999/xhtml">\n'+'\n'.join(urls)+'\n</urlset>\n')
(ROOT/'robots.txt').write_text('User-agent: *\nAllow: /\nSitemap: '+BASE+'/sitemap.xml\n')
print(f'Rendered {len(routes)*2+2} complete bilingual pages.')
