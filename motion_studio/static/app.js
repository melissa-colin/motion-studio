import * as THREE from 'three';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';
import { TransformControls } from 'three/addons/controls/TransformControls.js';

// ====================================================================
//  i18n : dictionnaire FR / EN / 中文 (chinois simplifie)
// ====================================================================
const I18N = {
  fr: {
    'app.title':'Motion Studio', 'status.loading':'chargement…',
    'tab.clip':'Clip','tab.edit':'Édition','tab.floor':'Sol','tab.video':'Vidéo','tab.comments':'💬',
    'comments.title':'Commentaires','comments.you':'Ton nom','comments.send':'Envoyer',
    'comments.placeholder':'écrire un commentaire…','comments.empty':'aucun commentaire',
    'comments.disabled':'commentaires indisponibles pour les clips importés',
    'comments.sendfail':'✗ échec de l’envoi : ','comments.loadfail':'✗ chargement impossible : ',
    'clip.change':'Parcourir les clips chargés',
    'dancer.label':'Danseur',
    'global.title':'Global (tout le corps)','global.allframes':'Toutes les frames (décalage constant)',
    'global.width':'Largeur (X)','global.height':'Hauteur (Z)','global.depth':'Profond. (Y)',
    'global.step':'Pas (m)','global.reset':'Réinitialiser le déplacement',
    'global.hint':'⚠ Décalage constant = pas de tremblement. Tire le gizmo au bassin, ou utilise les boutons ±.',
    'stretch.mode':'Étirer le déplacement',
    'stretch.modehint':'Ancre le danseur au début du mouvement, puis va à la fin et place-le à la bonne distance : l’outil étire le déplacement entre les deux points en gardant la forme du mouvement.',
    'stretch.anchor':'Ancrer ici','stretch.setpt':'Poser/maj le point ici',
    'stretch.delpt':'Supprimer le point courant','stretch.clearpts':'Tout effacer',
    'stretch.curoff':'Décalage ici','stretch.pts':'Points cibles','stretch.nopts':'aucun point',
    'stretch.atframe':'à la frame','stretch.target':'cible',
    'joints.title':'Joints (détail par articulation)','joint.label':'Joint',
    'joint.reset':'Annuler ce joint (frame)',
    'joint.hint':'Clique un joint en 3D · W translate · R rotate gizmo.',
    'refit.title':'Recalculer SMPL','refit.cur':'Refit frame courante','refit.all':'Refit tout',
    'refit.hint':'Recale le maillage SMPL sur les joints corrigés. « Frame courante » = rapide ; « Refit tout » = toutes les frames. Le maillage s’affiche via le bouton Maillage en haut de l’écran.',
    'correct.title':'Correcteur automatique','correct.btn':'Corriger le mouvement',
    'correct.hint':'Applique la correction automatique (sol → pieds → glisse) puis recharge le mouvement corrigé. Le 1er lancement prépare le modèle (~10-30 s).',
    'correct.input.raw':"Depuis l'original (brut)",'correct.input.edited':'Depuis mes modifs actuelles',
    'correct.running':'correction…','correct.done':'✓ corrigé en','correct.reload':'rechargement du motion corrigé…','correct.err':'✗ échec de la correction : ',
    'display.scene':'Scène','display.skeleton':'Squelette','display.mesh':'Maillage',
    'display.ghost':'Fantôme avant','display.ghost.tip':'Maillage du motion d’origine (avant édition/correction), superposé en semi-transparent pour comparer l’avant/après.',
    'mesh.gen':'génération du maillage…','mesh.ready':'✓ maillage affiché (frame courante)',
    'mesh.noBackend':'maillage indisponible pour ce clip (ouvre un clip via « Parcourir les clips chargés »)',
    'buffer.caching':'mise en cache du clip… $pct %',
    'buffer.gate':'Mise en cache du clip… $pct %\n(lecture fluide une fois terminé)',
    'overlay.skip':'Passer',
    'metrics.title':'Métriques (physique)','metrics.head.ref':'départ','metrics.head.cur':'actuel',
    'metrics.whole':'tout le clip','metrics.computing':'calcul…','metrics.clipbtn':'recalculer',
    'metrics.setref':'Définir comme départ','metrics.setref.tip':'Fige les métriques actuelles comme référence (colonne « départ »)',
    'metrics.setref.done':'départ défini sur les métriques actuelles','metrics.setref.none':'rien à figer : clique d’abord « recalculer »',
    'metrics.clipdone':'clip entier','metrics.hint':'vert = amélioré · rouge = empiré · vs métriques de référence',
    'metrics.float':'Flottement','metrics.penetrate':'Pénétration sol','metrics.skate':'Skate','metrics.pfc':'PFC',
    'metrics.self_pen':'Auto-pén.','metrics.inter_pen':'Inter-pén.','metrics.jitter':'Jitter',
    'metrics.off':'masqué','metrics.waiting':'modifie puis « recalculer » pour comparer',
    'metrics.stale':'modifié — clique « recalculer »',
    'metrics.pristine':'non modifié — identique au pipeline hors-outil',
    // messages d'etat (refit / sauvegarde / picker / chargement)
    'js.refit.run':'calcul SMPL en cours ($label)… ça peut prendre du temps',
    'js.refit.ok':'✓ SMPL recalé ($label) — erreur joints $eb→$ea m, $dt s. ',
    'js.refit.activate':'Active « Maillage » pour voir.',
    'js.refit.fail':'✗ refit échoué : ',
    'js.save.run':'refit SMPL + écriture du .pkl… (peut prendre quelques s)',
    'js.save.ok':'✓ sauvé : ','js.save.poses':'poses','js.save.trans':'trans','js.save.jointerr':'erreur joints',
    'js.save.untouched':"L'original n'a pas été touché.",
    'js.save.example':'✗ clip exemple (chemin direct) : ouvre un vrai clip via « Changer de clip » pour sauver un .pkl.',
    'js.save.fail':'✗ sauvegarde échouée : ',
    'js.load.overlay':'Conversion / chargement de « $name »…\n(FK + recalage vidéo si dispo)',
    'js.picker.loadlist':'chargement de la liste…',
    'js.picker.count':'$count clips',
    'js.picker.fail':'échec /clips : ','js.picker.nomatch':'aucun clip ne correspond.',
    'js.floor.example':'✗ clip exemple (chemin direct) : ouvre un vrai clip via « Changer de clip ».',
    'display.floor':'Sol estimé','display.floordist':'Distance au sol','display.view':'Vue',
    'view.front':'Face','view.side':'Côté','view.top':'Dessus',
    'view.back':'Dos','view.left':'Gauche','view.right':'Droite','view.bottom':'Dessous',
    'play.toggle':'Lecture / Pause','frame.slider':'Position dans la timeline (frame)',
    'bg.title':'Vidéo de fond','bg.visible':'Visible','bg.move':'Mode souris','bg.movebtn':'Déplacer fond',
    'bg.posx':'Pos X','bg.posy':'Pos Y (prof.)','bg.posz':'Pos Z','bg.scale':'Échelle','bg.opacity':'Opacité',
    'bg.removebg':'Retirer le fond',
    'bg.time.title':'Décalage temporel','bg.time.instant':'Instant vidéo (s)',
    'bg.time.hint':'Le fond doit se synchroniser avec les danseurs 3D. Fais glisser jusqu’à ce que la vidéo colle aux SMPL.',
    'bg.time.reextract':'Ré-extraire le fond','bg.time.extracting':'ré-extraction…',
    'bg.time.done':'fond ré-extrait','bg.time.novideo':'pas de vidéo pour ce clip',
    'bg.import.title':'Importer / remplacer le média',
    'bg.import.video':'Vidéo','bg.import.music':'Musique','bg.import.replace':'Importer / remplacer',
    'bg.import.nofile':'choisis d’abord un fichier','bg.import.uploading':'envoi…',
    'bg.import.video.done':'vidéo importée','bg.import.music.done':'musique importée',
    'bg.import.fail':'échec de l’import : ',
    'save.title':'Sauvegarder la GT','save.btn':'Sauvegarder le clip corrigé (.pkl)',
    'save.hint':'Refait le SMPL sur les joints corrigés puis écrit un nouveau .pkl (smpl_poses + root_trans, même format qu’AIOZ) dans GDance_gt_corrected/. L’original n’est jamais modifié. C’est la sortie principale.',
    'save.dirty':'Enregistrer (.motion)','save.saved':'✓ Enregistré (.motion)','save.saving':'sauvegarde…',
    'save.tip':'Enregistrer la session dans le .motion (Ctrl+S)',
    'export.pkl':'Exporter (.pkl)','export.pkl.tip':'Télécharger le .pkl corrigé (Ctrl+Maj+S)',
    'export.preparing':'préparation…','export.done':'✓ téléchargé','export.fail':'✗ export échoué : ',
    // sauvegarde .motion (session) — voir saveBundle()
    'bundle.save':'Enregistrer (.motion)','bundle.save.tip':'Enregistrer la session (joints édités + placement vidéo + commentaires + métriques) dans un bundle .motion (Ctrl+S)',
    'bundle.save.run':'écriture du .motion…','bundle.save.ok':'✓ session enregistrée : ',
    'bundle.save.fail':'✗ enregistrement échoué : ',
    'bundle.save.noclip':'✗ ouvre un vrai clip avant d’enregistrer un .motion.',
    // import d'un dossier dataset (GDance-style) -> bundles .motion — voir importFolder()
    'folder.title':'Charger un dossier','folder.summary':'Convertir un dossier dataset en clips',
    'folder.dir':'Dossier','folder.dir.ph':'/chemin/vers/dossier_dataset',
    'folder.pkl':'Pkl','folder.videos':'Vidéos','folder.audio':'Audio',
    'folder.go':'Importer le dossier','folder.run':'import en cours…',
    'folder.ok':'✓ importé : ','folder.fail':'✗ import échoué : ',
    'folder.nodir':'✗ indique un chemin de dossier.',
    'folder.progress':'import $done/$total$failed$current',  // ex : import 12/40 · 1 échec · clip_x
    'folder.hint':'Champs optionnels : laisse vide pour utiliser le dossier configuré par défaut. Chaque .pkl devient un projet .motion (vidéo + audio appariés par nom).',
    // trois points d'entree de chargement (onglet Clip) — voir openPklPicker/openPicker/openFolderDialog
    'load.file':'Charger un fichier','load.project':'Charger un projet','load.folder':'Charger un dossier',
    // liste unifiee des projets .motion — voir renderProjectList()
    'load.mesh':'Maillage','load.motion':'Mouvement','load.bg':'Fond',
    'clip.loading':'Chargement du clip…',
    'pkl.title':'Charger un fichier (.pkl)','pkl.filter':'filtrer…',
    'pkl.count':'$count fichiers','pkl.none':'aucun fichier .pkl dans le dossier configuré.',
    'pkl.importing':'conversion de $name…',
    'proj.title':'Projets','proj.search':'filtrer (nom, clip source…)',
    'proj.prev':'Précédent','proj.next':'Suivant','proj.refresh':'Rafraîchir',
    'proj.count':'$count projets','proj.none':'aucun projet .motion. Importe un fichier ou un dossier.',
    'proj.metrics.recalc':'recalculer les métriques',
    'proj.metrics.job':'métriques $done/$total$failed',  // ex : métriques 312/1624 · 2 échecs
    'col.name':'Nom','col.source':'Clip source','col.video':'Vidéo','col.music':'Musique','col.mtime':'Date',
    'col.tags':'Tags','col.pending':'métrique en cours…',
    'tags.add':'＋ tag','tags.placeholder':'nouveau tag…','tags.remove':'retirer',
    'tags.filter':'filtrer par tag :','tags.all':'tous',
    // bundles .motion listés dans le sélecteur de clip — voir renderClipList()
    'tag.bundle':'.motion','tag.video':'vidéo','tag.novideo':'sans vidéo','ws.loading':'chargement de l’espace de travail…',
    'undo':'Annuler (Ctrl+Z)','redo':'Rétablir (Ctrl+Y)',
    'picker.title':'Choisir un clip','picker.filter':'filtrer (ytid, segment…)','picker.close':'Fermer',
    'picker.onlycorrected':'déjà corrigés','tag.corrected':'corrigé',
    'src.title':'Ce clip a déjà une version corrigée',
    'src.original':'Ouvrir l’original','src.original.sub':'repartir de zéro',
    'src.corrected':'Ouvrir la version corrigée','src.corrected.sub':'poursuivre la correction',
    'src.cancel':'Annuler','source.editing.corrected':'édition de la version corrigée',
    'sort.label':'Trier :','sort.az':'A→Z',
    'sort.float':'Flottement','sort.penetrate':'Pénétration sol','sort.skate':'Skate','sort.pfc':'PFC',
    'sort.self_pen':'Auto-pén','sort.inter_pen':'Inter-pén','sort.jitter':'Jitter',
    'hud.click':'sélection joint','hud.gizmo':'translate/rotate gizmo','hud.play':'play','hud.frame':'frame',
    'floor.none':'pas de sol estimé pour ce clip','floor.tilt':'inclinaison',
    'floor.correct.title':'Corriger le sol','floor.variant':'Variante',
    'floor.var.corrected':'Corrigé','floor.var.raw':'Brut','floor.var.manual':'Manuel',
    'floor.editmode':'Corriger le sol','floor.tiltx':'Inclinaison X (°)','floor.tilty':'Inclinaison Y (°)','floor.heightm':'Hauteur (m)',
    'floor.reset':'Réinitialiser','floor.save':'Enregistrer le sol corrigé',
    'floor.hint':'En mode correction : un repère 3D apparaît sur le damier — rotation pour incliner, flèche Z pour monter/descendre. Ou édite les champs ci-dessus. « Enregistrer » écrit le sol manuel pour ce clip.',
    'floor.saving':'enregistrement du sol…','floor.saved':'✓ sol enregistré, inclinaison','floor.saveerr':'✗ échec enregistrement : ',
    'floor.recompute':'Recalculer le sol','floor.recomputing':'calcul du sol…',
    'floor.recomputed':'✓ sol recalculé, inclinaison','floor.recomputeerr':'✗ échec du recalcul : ',
    'floor.editon':'mode correction actif','floor.editoff':'corriger le sol',
    'video.with':'avec vidéo de fond','video.without':'sans vidéo (squelette seul)',
    'msg.pickClip':'choisis un clip…','msg.dancers':'danseurs','msg.frame':'frame','msg.frames':'frames','msg.novideo':' (sans vidéo)',
    'music.muted':'Son coupé — clique pour écouter','music.on':'Son activé — clique pour couper',
    'music.none':'pas de musique pour ce clip',
    'tag.custom':'importé',
    // ecran d'accueil (aucun clip ouvert)
    'empty.title':'Aucun clip ouvert',
    'empty.sub':'Choisis un clip pour commencer.',
    'empty.browse':'Parcourir les clips chargés','empty.browse.sub':'ouvrir un clip déjà disponible',
    'empty.folder':'Ouvrir un dossier','empty.folder.sub':'convertir un dossier dataset en clips',
    'empty.import':'Importer un .pkl','empty.import.sub':'ouvrir ton propre fichier de mouvement',
    // confirmation avant correction destructive (efface les modifs en cours)
    'confirm.correct.title':'Lancer la correction automatique ?',
    'confirm.correct.body':'Tu as des modifications non sauvegardées. La correction va les remplacer. Tu pourras revenir en arrière avec Annuler (Ctrl+Z).',
    'confirm.ok':'Corriger','confirm.cancel':'Annuler',
    // overlay « occupé » pendant les opérations longues
    'busy.correct':'correction du mouvement…','busy.refit':'recalcul SMPL…',
    'busy.floor':'recalcul du sol…','busy.folder':'conversion du dossier…',
    'busy.load':'chargement…',
    // toasts (actions refusées quand aucun clip n'est ouvert)
    'gate.noclip':'Ouvre d’abord un clip (Parcourir les clips chargés).',
    // en-tête d'explication du sélecteur de clips
    'picker.explain':'Un clip déjà corrigé propose l’original (repartir de zéro) ou la version corrigée (poursuivre).',
    // panneau réglages (roue) + aide raccourcis (?) + fichiers récents + plugins
    'settings.tip':'Réglages','settings.title':'Réglages',
    'settings.lang.label':'Langue','settings.lang':'Langue de l’interface',
    'settings.scene.label':'Scène par défaut',
    'settings.data.label':'Dossiers source','settings.data.tip':'Réglé une fois, mémorisé entre les lancements — puis lance « motion-studio » sans argument.',
    'settings.data.apply':'Appliquer et mémoriser',
    'settings.data.applied':'✓ $pkl pkl · $proj projets',
    'settings.smpl.label':'SMPL',
    'browse.tip':'Parcourir','browse.title':'Choisir un dossier','browse.choose':'Choisir ce dossier',
    'browse.dataset':'✓ dataset','browse.empty':'(aucun sous-dossier)','browse.error':'erreur',
    'help.tip':'Raccourcis clavier (?)',
    // ---- barre de menus (chrome desktop) ----
    'menu.file':'Fichier','menu.edit':'Édition','menu.view':'Affichage',
    'menu.tools':'Outils','menu.settings':'Paramètres','menu.help':'Aide',
    'menu.undo':'Annuler','menu.redo':'Rétablir',
    'menu.metrics':'Métriques','menu.panel':'Panneau latéral',
    'menu.panel.show':'Afficher le panneau','menu.panel.hide':'Replier le panneau',
    'menu.shortcuts':'Raccourcis clavier','menu.about':'Version / À propos',
    'menu.about.body':'Motion Studio — éditeur de pose SMPL.',
    'menu.about.nover':'version inconnue','about.version':'Version :',
    // ---- infobulles (prose déplacée des paragraphes vers title=) ----
    'refit.tip':'Recale le maillage SMPL sur les joints corrigés. Le maillage s’affiche via « Maillage » (menu Affichage).',
    'correct.tip':'Correction automatique (sol → pieds → glisse) puis recharge. 1er lancement ~10-30 s.',
    'floor.recompute.tip':'Recalcule le sol sur l’état édité courant.',
    'shortcuts.title':'Raccourcis clavier','shortcuts.close':'Fermer',
    'shortcuts.translate':'Outil translation (gizmo)','shortcuts.rotate':'Outil rotation (gizmo)',
    'shortcuts.grab':'Translation (alias de W)','shortcuts.space':'Espace','shortcuts.play':'Lecture / Pause',
    'shortcuts.step':'Frame précédente / suivante','shortcuts.save':'Enregistrer la session (.motion)',
    'shortcuts.export':'Exporter le .pkl','shortcuts.undo':'Annuler','shortcuts.redo':'Rétablir',
    'shortcuts.help':'Afficher cette aide','shortcuts.esc':'Fermer une fenêtre / quitter un mode',
    'recent.title':'Récemment ouverts',
    'plugin.corrector':'Correcteur','plugin.metrics':'Métriques','plugin.none':'(aucun)',
    'plugin.footer':'Correcteur $corr · Métriques $met',
    'autosave.restored':'brouillon de session restauré',
    'unsaved.guard':'Tu as des modifications non enregistrées.',
  },
  en: {
    'app.title':'Motion Studio','status.loading':'loading…',
    'tab.clip':'Clip','tab.edit':'Edit','tab.floor':'Floor','tab.video':'Video','tab.comments':'💬',
    'comments.title':'Comments','comments.you':'Your name','comments.send':'Send',
    'comments.placeholder':'write a comment…','comments.empty':'no comments',
    'comments.disabled':'comments unavailable for imported clips',
    'comments.sendfail':'✗ send failed: ','comments.loadfail':'✗ load failed: ',
    'clip.change':'Browse loaded clips',
    'dancer.label':'Dancer',
    'global.title':'Global (whole body)','global.allframes':'All frames (constant offset)',
    'global.width':'Width (X)','global.height':'Height (Z)','global.depth':'Depth (Y)',
    'global.step':'Step (m)','global.reset':'Reset displacement',
    'global.hint':'⚠ Constant offset = no jitter. Drag the pelvis gizmo, or use the ± buttons.',
    'stretch.mode':'Stretch the displacement',
    'stretch.modehint':'Anchor the dancer at the start of the move, then go to the end and place it at the right distance: the tool stretches the displacement between the two points while keeping the shape of the motion.',
    'stretch.anchor':'Anchor here','stretch.setpt':'Set/update point here',
    'stretch.delpt':'Delete current point','stretch.clearpts':'Clear all',
    'stretch.curoff':'Offset here','stretch.pts':'Target points','stretch.nopts':'no point',
    'stretch.atframe':'at frame','stretch.target':'target',
    'joints.title':'Joints (per-joint detail)','joint.label':'Joint',
    'joint.reset':'Undo this joint (frame)',
    'joint.hint':'Click a joint in 3D · W translate · R rotate gizmo.',
    'refit.title':'Recompute SMPL','refit.cur':'Refit current frame','refit.all':'Refit all',
    'refit.hint':'Re-fits the SMPL mesh onto the corrected joints. “Current frame” = fast; “Refit all” = every frame. The mesh shows up via the Mesh button at the top of the screen.',
    'correct.title':'Automatic corrector','correct.btn':'Correct the motion',
    'correct.hint':'Runs the automatic correction (floor → feet → skate), then reloads the corrected motion. The first run prepares the model (~10-30 s).',
    'correct.input.raw':'From the raw original','correct.input.edited':'From my current edits',
    'correct.running':'correcting…','correct.done':'✓ corrected in','correct.reload':'reloading corrected motion…','correct.err':'✗ correction failed: ',
    'display.scene':'Scene','display.skeleton':'Skeleton','display.mesh':'Mesh',
    'display.ghost':'Ghost (before)','display.ghost.tip':'Original motion mesh (before editing/correction), overlaid semi-transparent to compare before/after.',
    'mesh.gen':'generating mesh…','mesh.ready':'✓ mesh shown (current frame)',
    'mesh.noBackend':'mesh unavailable for this clip (open one via “Browse loaded clips”)',
    'buffer.caching':'caching clip… $pct %',
    'buffer.gate':'Caching clip… $pct %\n(smooth playback once done)',
    'overlay.skip':'Skip',
    'metrics.title':'Metrics (physics)','metrics.head.ref':'start','metrics.head.cur':'current',
    'metrics.whole':'whole clip','metrics.computing':'computing…','metrics.clipbtn':'recompute',
    'metrics.setref':'Set as start','metrics.setref.tip':'Freeze current metrics as the reference (the “start” column)',
    'metrics.setref.done':'start set to current metrics','metrics.setref.none':'nothing to freeze: click “recompute” first',
    'metrics.clipdone':'whole clip','metrics.hint':'green = improved · red = worse · vs reference metrics',
    'metrics.float':'Float','metrics.penetrate':'Floor penetration','metrics.skate':'Skate','metrics.pfc':'PFC',
    'metrics.self_pen':'Self-pen.','metrics.inter_pen':'Inter-pen.','metrics.jitter':'Jitter',
    'metrics.off':'hidden','metrics.waiting':'edit, then “recompute” to compare',
    'clip.loading':'Loading clip…',
    'metrics.stale':'edited — click “recompute”',
    'metrics.pristine':'unmodified — identical to the offline pipeline',
    'js.refit.run':'computing SMPL ($label)… this can take a while',
    'js.refit.ok':'✓ SMPL refitted ($label) — joint error $eb→$ea m, $dt s. ',
    'js.refit.activate':'Turn on “Mesh” to see it.',
    'js.refit.fail':'✗ refit failed: ',
    'js.save.run':'refit SMPL + writing the .pkl… (may take a few s)',
    'js.save.ok':'✓ saved: ','js.save.poses':'poses','js.save.trans':'trans','js.save.jointerr':'joint error',
    'js.save.untouched':'The original was not modified.',
    'js.save.example':'✗ example clip (direct path): open a real clip via “Change clip” to save a .pkl.',
    'js.save.fail':'✗ save failed: ',
    'js.load.overlay':'Converting / loading “$name”…\n(FK + video alignment if available)',
    'js.picker.loadlist':'loading list…',
    'js.picker.count':'$count clips',
    'js.picker.fail':'/clips failed: ','js.picker.nomatch':'no matching clip.',
    'js.floor.example':'✗ example clip (direct path): open a real clip via “Change clip”.',
    'display.floor':'Estimated floor','display.floordist':'Floor distance','display.view':'View',
    'view.front':'Front','view.side':'Side','view.top':'Top',
    'view.back':'Back','view.left':'Left','view.right':'Right','view.bottom':'Bottom',
    'play.toggle':'Play / Pause','frame.slider':'Timeline position (frame)',
    'bg.title':'Background video','bg.visible':'Visible','bg.move':'Mouse mode','bg.movebtn':'Move background',
    'bg.posx':'Pos X','bg.posy':'Pos Y (depth)','bg.posz':'Pos Z','bg.scale':'Scale','bg.opacity':'Opacity',
    'bg.removebg':'Remove background',
    'bg.time.title':'Time offset','bg.time.instant':'Video time (s)',
    'bg.time.hint':'The background must sync with the 3D dancers. Slide until the video matches the SMPL meshes.',
    'bg.time.reextract':'Re-extract background','bg.time.extracting':'re-extracting…',
    'bg.time.done':'background re-extracted','bg.time.novideo':'no video for this clip',
    'bg.import.title':'Import / replace media',
    'bg.import.video':'Video','bg.import.music':'Music','bg.import.replace':'Import / replace',
    'bg.import.nofile':'pick a file first','bg.import.uploading':'uploading…',
    'bg.import.video.done':'video imported','bg.import.music.done':'music imported',
    'bg.import.fail':'import failed: ',
    'save.title':'Save GT','save.btn':'Save corrected clip (.pkl)',
    'save.hint':'Re-fits SMPL on the corrected joints then writes a new .pkl (smpl_poses + root_trans, same format as AIOZ) in GDance_gt_corrected/. The original is never modified. This is the main output.',
    'save.dirty':'Save (.motion)','save.saved':'✓ Saved (.motion)','save.saving':'saving…',
    'save.tip':'Save the session to the .motion bundle (Ctrl+S)',
    'export.pkl':'Export (.pkl)','export.pkl.tip':'Download the corrected .pkl (Ctrl+Shift+S)',
    'export.preparing':'preparing…','export.done':'✓ downloaded','export.fail':'✗ export failed: ',
    // .motion (session) save — see saveBundle()
    'bundle.save':'Save (.motion)','bundle.save.tip':'Save the session (edited joints + video placement + comments + metrics) to a .motion bundle (Ctrl+S)',
    'bundle.save.run':'writing the .motion…','bundle.save.ok':'✓ session saved: ',
    'bundle.save.fail':'✗ save failed: ',
    'bundle.save.noclip':'✗ open a real clip before saving a .motion.',
    // dataset folder import (GDance-style) -> .motion bundles — see importFolder()
    'folder.title':'Open a folder','folder.summary':'Convert a dataset folder into clips',
    'folder.dir':'Folder','folder.dir.ph':'/path/to/dataset_folder',
    'folder.go':'Open folder','folder.run':'converting… (this can take a while)',
    'folder.ok':'✓ converted: ','folder.fail':'✗ conversion failed: ',
    'folder.nodir':'✗ enter a folder path.',
    'folder.hint':'GDance-style folder expected (motions_smpl/, musics/, smpl_videos/). Each clip becomes a .motion bundle in the workspace.',
    // .motion bundles listed in the clip picker — see renderClipList()
    'tag.bundle':'.motion','tag.video':'video','tag.novideo':'no video','ws.loading':'loading the workspace…',
    'undo':'Undo (Ctrl+Z)','redo':'Redo (Ctrl+Y)',
    'picker.title':'Choose a clip','picker.filter':'filter (ytid, segment…)','picker.close':'Close',
    'picker.onlycorrected':'corrected only','tag.corrected':'corrected',
    'src.title':'This clip already has a corrected version',
    'src.original':'Open the original','src.original.sub':'start from scratch',
    'src.corrected':'Open the corrected version','src.corrected.sub':'continue correcting',
    'src.cancel':'Cancel','source.editing.corrected':'editing the corrected version',
    'sort.label':'Sort:','sort.az':'A→Z',
    'sort.float':'Float','sort.penetrate':'Penetration','sort.skate':'Skate','sort.pfc':'PFC',
    'sort.self_pen':'Self-pen','sort.inter_pen':'Inter-pen','sort.jitter':'Jitter',
    'hud.click':'select joint','hud.gizmo':'translate/rotate gizmo','hud.play':'play','hud.frame':'frame',
    'floor.none':'no estimated floor for this clip','floor.tilt':'tilt',
    'floor.correct.title':'Correct the floor','floor.variant':'Variant',
    'floor.var.corrected':'Corrected','floor.var.raw':'Raw','floor.var.manual':'Manual',
    'floor.editmode':'Correct the floor','floor.tiltx':'Tilt X (°)','floor.tilty':'Tilt Y (°)','floor.heightm':'Height (m)',
    'floor.reset':'Reset','floor.save':'Save corrected floor',
    'floor.hint':'In correction mode: a 3D gizmo appears on the checkerboard — rotate to tilt, drag the Z arrow to raise/lower. Or edit the fields above. “Save” writes the manual floor for this clip.',
    'floor.saving':'saving floor…','floor.saved':'✓ floor saved, tilt','floor.saveerr':'✗ save failed: ',
    'floor.recompute':'Recompute floor','floor.recomputing':'computing floor…',
    'floor.recomputed':'✓ floor recomputed, tilt','floor.recomputeerr':'✗ recompute failed: ',
    'floor.editon':'correction mode on','floor.editoff':'correct the floor',
    'video.with':'with background video','video.without':'no video (skeleton only)',
    'msg.pickClip':'choose a clip…','msg.dancers':'dancers','msg.frame':'frame','msg.frames':'frames','msg.novideo':' (no video)',
    'music.muted':'Sound off — click to listen','music.on':'Sound on — click to mute',
    'music.none':'no music for this clip',
    'tag.custom':'imported',
    // folder import extra fields + progress
    'folder.pkl':'Pkl','folder.videos':'Videos','folder.audio':'Audio',
    'folder.progress':'import $done/$total$failed$current',
    // three load entry points (Clip tab)
    'load.file':'Load a file','load.project':'Load a project','load.folder':'Load a folder',
    // unified .motion project list
    'load.mesh':'Mesh','load.motion':'Motion','load.bg':'Background',
    'pkl.title':'Load a file (.pkl)','pkl.filter':'filter…',
    'pkl.count':'$count files','pkl.none':'no .pkl file in the configured folder.',
    'pkl.importing':'converting $name…',
    'proj.title':'Projects','proj.search':'filter (name, source clip…)',
    'proj.prev':'Previous','proj.next':'Next','proj.refresh':'Refresh',
    'proj.count':'$count projects','proj.none':'no .motion project. Import a file or a folder.',
    'proj.metrics.recalc':'recompute metrics',
    'proj.metrics.job':'metrics $done/$total$failed',
    'col.name':'Name','col.source':'Source clip','col.video':'Video','col.music':'Music','col.mtime':'Date',
    'col.tags':'Tags','col.pending':'metric in progress…',
    'tags.add':'＋ tag','tags.placeholder':'new tag…','tags.remove':'remove',
    'tags.filter':'filter by tag:','tags.all':'all',
    'busy.load':'loading…',
    'settings.data.label':'Source folders','settings.data.tip':'Set once, remembered across launches — then run “motion-studio” with no arguments.',
    'settings.data.apply':'Apply & remember',
    'settings.data.applied':'✓ $pkl pkl · $proj projects',
    'settings.smpl.label':'SMPL',
    'browse.tip':'Browse','browse.title':'Choose a folder','browse.choose':'Choose this folder',
    'browse.dataset':'✓ dataset','browse.empty':'(no sub-folder)','browse.error':'error',
    // menu bar (desktop chrome)
    'menu.file':'File','menu.edit':'Edit','menu.view':'View',
    'menu.tools':'Tools','menu.settings':'Settings','menu.help':'Help',
    'menu.undo':'Undo','menu.redo':'Redo',
    'menu.metrics':'Metrics','menu.panel':'Side panel',
    'menu.panel.show':'Show the panel','menu.panel.hide':'Collapse the panel',
    'menu.shortcuts':'Keyboard shortcuts','menu.about':'Version / About',
    'menu.about.body':'Motion Studio — SMPL pose editor.',
    'menu.about.nover':'unknown version','about.version':'Version:',
    // tooltips (prose moved from paragraphs to title=)
    'refit.tip':'Re-fits the SMPL mesh onto the corrected joints. The mesh shows up via “Mesh” (View menu).',
    'correct.tip':'Automatic correction (floor → feet → skate) then reload. First run ~10-30 s.',
    'floor.recompute.tip':'Recompute the floor on the current edited state.',
    'empty.title':'No clip open',
    'empty.sub':'Pick a clip to get started.',
    'empty.browse':'Browse loaded clips','empty.browse.sub':'open a clip already available',
    'empty.folder':'Open a folder','empty.folder.sub':'convert a dataset folder into clips',
    'empty.import':'Import a .pkl','empty.import.sub':'open your own motion file',
    'confirm.correct.title':'Run the auto-corrector?',
    'confirm.correct.body':'You have unsaved edits. The correction will replace them. You can revert with Undo (Ctrl+Z).',
    'confirm.ok':'Correct','confirm.cancel':'Cancel',
    'busy.correct':'correcting motion…','busy.refit':'recomputing SMPL…',
    'busy.floor':'recomputing floor…','busy.folder':'converting folder…',
    'gate.noclip':'Open a clip first (Browse loaded clips).',
    'picker.explain':'A corrected clip lets you open the original (start over) or the corrected version (keep going).',
    'settings.tip':'Settings','settings.title':'Settings',
    'settings.lang.label':'Language','settings.lang':'Interface language',
    'settings.scene.label':'Default scene',
    'help.tip':'Keyboard shortcuts (?)',
    'shortcuts.title':'Keyboard shortcuts','shortcuts.close':'Close',
    'shortcuts.translate':'Translate tool (gizmo)','shortcuts.rotate':'Rotate tool (gizmo)',
    'shortcuts.grab':'Translate (alias of W)','shortcuts.space':'Space','shortcuts.play':'Play / Pause',
    'shortcuts.step':'Previous / next frame','shortcuts.save':'Save the session (.motion)',
    'shortcuts.export':'Export the .pkl','shortcuts.undo':'Undo','shortcuts.redo':'Redo',
    'shortcuts.help':'Show this help','shortcuts.esc':'Close a dialog / leave a mode',
    'recent.title':'Recently opened',
    'plugin.corrector':'Corrector','plugin.metrics':'Metrics','plugin.none':'(none)',
    'plugin.footer':'Corrector $corr · Metrics $met',
    'autosave.restored':'session draft restored',
    'unsaved.guard':'You have unsaved changes.',
  },
  zh: {
    'app.title':'Motion Studio','status.loading':'加载中…',
    'tab.clip':'片段','tab.edit':'编辑','tab.floor':'地面','tab.video':'视频','tab.comments':'💬',
    'comments.title':'评论','comments.you':'你的名字','comments.send':'发送',
    'comments.placeholder':'写一条评论…','comments.empty':'暂无评论',
    'comments.disabled':'导入的片段不支持评论',
    'comments.sendfail':'✗ 发送失败：','comments.loadfail':'✗ 加载失败：',
    'clip.change':'浏览已加载片段',
    'dancer.label':'舞者',
    'global.title':'整体（全身）','global.allframes':'所有帧（恒定偏移）',
    'global.width':'宽度 (X)','global.height':'高度 (Z)','global.depth':'深度 (Y)',
    'global.step':'步长 (米)','global.reset':'重置位移',
    'global.hint':'⚠ 恒定偏移 = 无抖动。拖动骨盆控制器，或使用 ± 按钮。',
    'stretch.mode':'拉伸位移',
    'stretch.modehint':'在动作开始处锚定舞者，然后跳到结束帧并把他放到正确的距离：工具会在两点之间拉伸位移，同时保持动作的形态。',
    'stretch.anchor':'在此锚定','stretch.setpt':'在此设置/更新点',
    'stretch.delpt':'删除当前点','stretch.clearpts':'全部清除',
    'stretch.curoff':'此处偏移','stretch.pts':'目标点','stretch.nopts':'无点',
    'stretch.atframe':'在第','stretch.target':'目标',
    'joints.title':'关节（逐关节细节）','joint.label':'关节',
    'joint.reset':'撤销此关节（当前帧）',
    'joint.hint':'在三维视图中点击关节 · W 平移 · R 旋转控制器。',
    'refit.title':'重新计算 SMPL','refit.cur':'拟合当前帧','refit.all':'拟合全部',
    'refit.hint':'将 SMPL 网格重新拟合到修正后的关节。“当前帧”=快速；“拟合全部”=所有帧。网格通过屏幕顶部的“网格”按钮显示。',
    'correct.title':'自动校正器','correct.btn':'校正动作',
    'correct.hint':'运行自动校正（地面 → 脚 → 滑步），然后重新加载校正后的动作。首次运行会准备模型（约 10-30 秒）。',
    'correct.input.raw':'从原始数据（未处理）','correct.input.edited':'从我当前的修改',
    'correct.running':'校正中…','correct.done':'✓ 校正完成，用时','correct.reload':'正在重新加载校正后的动作…','correct.err':'✗ 校正失败：',
    'display.scene':'场景','display.skeleton':'骨架','display.mesh':'网格',
    'display.ghost':'原始幻影','display.ghost.tip':'原始动作网格（编辑/校正前），以半透明叠加显示，用于对比前后。',
    'mesh.gen':'正在生成网格…','mesh.ready':'✓ 已显示网格（当前帧）',
    'mesh.noBackend':'此片段无法生成网格（请通过“浏览已加载片段”打开一个片段）',
    'buffer.caching':'正在缓存片段… $pct %',
    'buffer.gate':'正在缓存片段… $pct %\n（完成后播放流畅）',
    'overlay.skip':'跳过',
    'metrics.title':'指标（物理）','metrics.head.ref':'初始','metrics.head.cur':'当前',
    'metrics.whole':'整段','metrics.computing':'计算中…','metrics.clipbtn':'重新计算',
    'metrics.setref':'设为初始','metrics.setref.tip':'将当前指标固定为参考（“初始”列）',
    'metrics.setref.done':'已将初始设为当前指标','metrics.setref.none':'暂无可固定的数据：请先点击“重新计算”',
    'metrics.clipdone':'整段','metrics.hint':'绿色 = 改善 · 红色 = 变差 · 对比参考指标',
    'metrics.float':'漂浮','metrics.penetrate':'地面穿透','metrics.skate':'滑步','metrics.pfc':'PFC',
    'metrics.self_pen':'自穿透','metrics.inter_pen':'互穿透','metrics.jitter':'抖动',
    'metrics.off':'隐藏','metrics.waiting':'修改后点击“重新计算”进行比较',
    'clip.loading':'正在加载片段…',
    'metrics.stale':'已修改 — 点击“重新计算”',
    'metrics.pristine':'未修改 — 与离线管线完全一致',
    'js.refit.run':'正在计算 SMPL（$label）… 可能需要一些时间',
    'js.refit.ok':'✓ 已重新拟合 SMPL（$label）— 关节误差 $eb→$ea 米，$dt 秒。',
    'js.refit.activate':'打开“网格”以查看。',
    'js.refit.fail':'✗ 拟合失败：',
    'js.save.run':'重新拟合 SMPL + 写入 .pkl…（可能需要几秒）',
    'js.save.ok':'✓ 已保存：','js.save.poses':'姿态','js.save.trans':'平移','js.save.jointerr':'关节误差',
    'js.save.untouched':'原文件未被修改。',
    'js.save.example':'✗ 示例片段（直接路径）：通过“切换片段”打开真实片段以保存 .pkl。',
    'js.save.fail':'✗ 保存失败：',
    'js.load.overlay':'正在转换 / 加载“$name”…\n（FK + 视频对齐（如可用））',
    'js.picker.loadlist':'正在加载列表…',
    'js.picker.count':'$count 个片段',
    'js.picker.fail':'/clips 失败：','js.picker.nomatch':'没有匹配的片段。',
    'js.floor.example':'✗ 示例片段（直接路径）：通过“切换片段”打开真实片段。',
    'display.floor':'估计地面','display.floordist':'离地距离','display.view':'视角',
    'view.front':'正面','view.side':'侧面','view.top':'顶部',
    'view.back':'背面','view.left':'左侧','view.right':'右侧','view.bottom':'底部',
    'play.toggle':'播放 / 暂停','frame.slider':'时间轴位置（帧）',
    'bg.title':'背景视频','bg.visible':'可见','bg.move':'鼠标模式','bg.movebtn':'移动背景',
    'bg.posx':'位置 X','bg.posy':'位置 Y（深度）','bg.posz':'位置 Z','bg.scale':'缩放','bg.opacity':'不透明度',
    'bg.removebg':'移除背景',
    'bg.time.title':'时间偏移','bg.time.instant':'视频时刻（秒）',
    'bg.time.hint':'背景必须与 3D 舞者同步。拖动滑块直到视频与 SMPL 对齐。',
    'bg.time.reextract':'重新提取背景','bg.time.extracting':'重新提取中…',
    'bg.time.done':'背景已重新提取','bg.time.novideo':'此片段没有视频',
    'bg.import.title':'导入 / 替换媒体',
    'bg.import.video':'视频','bg.import.music':'音乐','bg.import.replace':'导入 / 替换',
    'bg.import.nofile':'请先选择文件','bg.import.uploading':'上传中…',
    'bg.import.video.done':'视频已导入','bg.import.music.done':'音乐已导入',
    'bg.import.fail':'导入失败：',
    'save.title':'保存 GT','save.btn':'保存修正片段 (.pkl)',
    'save.hint':'在修正后的关节上重新拟合 SMPL，然后写入新的 .pkl（smpl_poses + root_trans，与 AIOZ 格式相同）到 GDance_gt_corrected/。原文件永不修改。这是主要输出。',
    'save.dirty':'保存 (.motion)','save.saved':'✓ 已保存 (.motion)','save.saving':'保存中…',
    'save.tip':'将会话保存到 .motion 文件 (Ctrl+S)',
    'export.pkl':'导出 (.pkl)','export.pkl.tip':'下载修正后的 .pkl (Ctrl+Shift+S)',
    'export.preparing':'准备中…','export.done':'✓ 已下载','export.fail':'✗ 导出失败：',
    // .motion（会话）保存 — 见 saveBundle()
    'bundle.save':'保存 (.motion)','bundle.save.tip':'将会话（已编辑关节 + 视频摆放 + 评论 + 指标）保存到 .motion 文件 (Ctrl+S)',
    'bundle.save.run':'正在写入 .motion…','bundle.save.ok':'✓ 会话已保存：',
    'bundle.save.fail':'✗ 保存失败：',
    'bundle.save.noclip':'✗ 保存 .motion 前请先打开真实片段。',
    // 数据集文件夹导入（GDance 风格）-> .motion 文件 — 见 importFolder()
    'folder.title':'打开文件夹','folder.summary':'转换数据集文件夹 (.motion)',
    'folder.dir':'文件夹','folder.dir.ph':'/数据集文件夹/路径',
    'folder.go':'转换文件夹','folder.run':'转换中…（可能需要一些时间）',
    'folder.ok':'✓ 已转换：','folder.fail':'✗ 转换失败：',
    'folder.nodir':'✗ 请输入文件夹路径。',
    'folder.hint':'需要 GDance 风格的文件夹（motions_smpl/、musics/、smpl_videos/）。每个片段会在工作区中变成一个 .motion 文件。',
    // 片段选择器中列出的 .motion 文件 — 见 renderClipList()
    'tag.bundle':'.motion','tag.video':'视频','tag.novideo':'无视频','ws.loading':'正在加载工作区…',
    'undo':'撤销 (Ctrl+Z)','redo':'重做 (Ctrl+Y)',
    'picker.title':'选择片段','picker.filter':'筛选（ytid、片段…）','picker.close':'关闭',
    'picker.onlycorrected':'仅已校正','tag.corrected':'已校正',
    'src.title':'该片段已有校正版本',
    'src.original':'打开原始版本','src.original.sub':'从头开始',
    'src.corrected':'打开校正版本','src.corrected.sub':'继续校正',
    'src.cancel':'取消','source.editing.corrected':'正在编辑校正版本',
    'sort.label':'排序：','sort.az':'A→Z',
    'sort.float':'漂浮','sort.penetrate':'穿地','sort.skate':'滑步','sort.pfc':'PFC',
    'sort.self_pen':'自穿','sort.inter_pen':'互穿','sort.jitter':'抖动',
    'hud.click':'选择关节','hud.gizmo':'平移/旋转控制器','hud.play':'播放','hud.frame':'帧',
    'floor.none':'该片段没有估计地面','floor.tilt':'倾角',
    'floor.correct.title':'校正地面','floor.variant':'变体',
    'floor.var.corrected':'已校正','floor.var.raw':'原始','floor.var.manual':'手动',
    'floor.editmode':'校正地面','floor.tiltx':'倾角 X (°)','floor.tilty':'倾角 Y (°)','floor.heightm':'高度 (米)',
    'floor.reset':'重置','floor.save':'保存校正后的地面',
    'floor.hint':'校正模式下：棋盘上出现三维控制器——旋转可倾斜，拖动 Z 箭头可升降。或编辑上方数值。“保存”会为该片段写入手动地面。',
    'floor.saving':'正在保存地面…','floor.saved':'✓ 地面已保存，倾角','floor.saveerr':'✗ 保存失败：',
    'floor.recompute':'重新计算地面','floor.recomputing':'正在计算地面…',
    'floor.recomputed':'✓ 地面已重新计算，倾角','floor.recomputeerr':'✗ 重新计算失败：',
    'floor.editon':'校正模式开启','floor.editoff':'校正地面',
    'video.with':'带背景视频','video.without':'无视频（仅骨架）',
    'msg.pickClip':'请选择一个片段…','msg.dancers':'舞者','msg.frame':'帧','msg.frames':'帧','msg.novideo':'（无视频）',
    'music.muted':'已静音 — 点击收听','music.on':'已开启声音 — 点击静音',
    'music.none':'此片段没有音乐',
    'tag.custom':'导入',
    // 文件夹导入的额外字段 + 进度
    'folder.pkl':'Pkl','folder.videos':'视频','folder.audio':'音频',
    'folder.progress':'导入 $done/$total$failed$current',
    // 三个加载入口（片段标签页）
    'load.file':'加载文件','load.project':'加载项目','load.folder':'加载文件夹',
    // 统一的 .motion 项目列表
    'load.mesh':'网格','load.motion':'动作','load.bg':'背景',
    'pkl.title':'加载文件 (.pkl)','pkl.filter':'筛选…',
    'pkl.count':'$count 个文件','pkl.none':'配置的文件夹中没有 .pkl 文件。',
    'pkl.importing':'正在转换 $name…',
    'proj.title':'项目','proj.search':'筛选（名称、源片段…）',
    'proj.prev':'上一个','proj.next':'下一个','proj.refresh':'刷新',
    'proj.count':'$count 个项目','proj.none':'没有 .motion 项目。请导入文件或文件夹。',
    'proj.metrics.recalc':'重新计算指标',
    'proj.metrics.job':'指标 $done/$total$failed',
    'col.name':'名称','col.source':'源片段','col.video':'视频','col.music':'音乐','col.mtime':'日期',
    'col.tags':'标签','col.pending':'指标计算中…',
    'tags.add':'＋ 标签','tags.placeholder':'新标签…','tags.remove':'移除',
    'tags.filter':'按标签筛选：','tags.all':'全部',
    'busy.load':'加载中…',
    'settings.data.label':'源文件夹','settings.data.tip':'设置一次，跨启动记忆——然后无需参数运行“motion-studio”。',
    'settings.data.apply':'应用并记住',
    'settings.data.applied':'✓ $pkl 个 pkl · $proj 个项目',
    'settings.smpl.label':'SMPL',
    'browse.tip':'浏览','browse.title':'选择文件夹','browse.choose':'选择此文件夹',
    'browse.dataset':'✓ 数据集','browse.empty':'（无子文件夹）','browse.error':'错误',
    // 菜单栏（桌面应用风格）
    'menu.file':'文件','menu.edit':'编辑','menu.view':'显示',
    'menu.tools':'工具','menu.settings':'设置','menu.help':'帮助',
    'menu.undo':'撤销','menu.redo':'重做',
    'menu.metrics':'指标','menu.panel':'侧边面板',
    'menu.panel.show':'显示面板','menu.panel.hide':'收起面板',
    'menu.shortcuts':'键盘快捷键','menu.about':'版本 / 关于',
    'menu.about.body':'Motion Studio — SMPL 姿态编辑器。',
    'menu.about.nover':'版本未知','about.version':'版本：',
    // 提示（从段落移到 title= 的说明文字）
    'refit.tip':'将 SMPL 网格重新拟合到修正后的关节。网格通过“网格”（显示菜单）显示。',
    'correct.tip':'自动校正（地面 → 脚 → 滑步）然后重新加载。首次运行约 10-30 秒。',
    'floor.recompute.tip':'在当前编辑状态上重新计算地面。',
    'empty.title':'未打开任何片段',
    'empty.sub':'选择一个片段开始。',
    'empty.browse':'浏览已加载片段','empty.browse.sub':'打开一个已有片段',
    'empty.folder':'打开文件夹','empty.folder.sub':'将数据集文件夹转换为片段',
    'empty.import':'导入 .pkl','empty.import.sub':'打开你自己的动作文件',
    'confirm.correct.title':'运行自动校正？',
    'confirm.correct.body':'你有未保存的修改。校正将替换它们。可用撤销（Ctrl+Z）恢复。',
    'confirm.ok':'校正','confirm.cancel':'取消',
    'busy.correct':'正在校正动作…','busy.refit':'正在重算 SMPL…',
    'busy.floor':'正在重算地面…','busy.folder':'正在转换文件夹…',
    'gate.noclip':'请先打开一个片段（浏览已加载片段）。',
    'picker.explain':'已校正的片段可打开原始版本（从头开始）或已校正版本（继续编辑）。',
    'settings.tip':'设置','settings.title':'设置',
    'settings.lang.label':'语言','settings.lang':'界面语言',
    'settings.scene.label':'默认场景',
    'help.tip':'键盘快捷键 (?)',
    'shortcuts.title':'键盘快捷键','shortcuts.close':'关闭',
    'shortcuts.translate':'平移工具（控制器）','shortcuts.rotate':'旋转工具（控制器）',
    'shortcuts.grab':'平移（W 的别名）','shortcuts.space':'空格','shortcuts.play':'播放 / 暂停',
    'shortcuts.step':'上一帧 / 下一帧','shortcuts.save':'保存会话 (.motion)',
    'shortcuts.export':'导出 .pkl','shortcuts.undo':'撤销','shortcuts.redo':'重做',
    'shortcuts.help':'显示此帮助','shortcuts.esc':'关闭窗口 / 退出模式',
    'recent.title':'最近打开',
    'plugin.corrector':'校正器','plugin.metrics':'指标','plugin.none':'（无）',
    'plugin.footer':'校正器 $corr · 指标 $met',
    'autosave.restored':'已恢复会话草稿',
    'unsaved.guard':'你有未保存的修改。',
  },
};
let LANG = localStorage.getItem('pe.lang') || 'en';
function t(key){ return (I18N[LANG] && I18N[LANG][key]) || (I18N.fr[key]) || key; }
// t() avec interpolation de variables $nom (ex tf('js.refit.ok',{label,eb,ea,dt})).
function tf(key, vars){
  let s=t(key);
  if(vars) for(const k in vars){ s=s.split('$'+k).join(vars[k]); }
  return s;
}
function applyLang(lang){
  LANG = (I18N[lang] ? lang : 'en');
  localStorage.setItem('pe.lang', LANG);
  document.documentElement.lang = LANG;
  document.querySelectorAll('[data-i18n]').forEach(el=>{ el.textContent = t(el.getAttribute('data-i18n')); });
  document.querySelectorAll('[data-i18n-ph]').forEach(el=>{ el.placeholder = t(el.getAttribute('data-i18n-ph')); });
  document.querySelectorAll('[data-i18n-title]').forEach(el=>{ el.title = t(el.getAttribute('data-i18n-title')); });
  // libelles accessibles (aria-label) localises : boutons icone, vues, slider…
  document.querySelectorAll('[data-i18n-aria]').forEach(el=>{ el.setAttribute('aria-label', t(el.getAttribute('data-i18n-aria'))); });
  const ls=$('lang-sel'); if(ls) ls.value=LANG;
  updateHUD();
  if(typeof renderComments==='function') renderComments();   // dates/empty localises
  if(DATA){ updateClipInfo(); }
  if(typeof updateMusicBtn==='function') updateMusicBtn();
  if(typeof renderSavePill==='function') renderSavePill();   // pastille = etat reel (pas le data-i18n brut)
  if(typeof renderMetricsPanel==='function') renderMetricsPanel();  // libelles metriques re-localises
  if(typeof renderEmptyState==='function') renderEmptyState();      // empty-state (re)traduit si pas de clip
  const sl=$('set-lang'); if(sl) sl.value=LANG;                     // selecteur de langue du panneau reglages
  if(typeof renderPluginInfo==='function') renderPluginInfo();      // pied "plugins actifs" re-localise
  if(typeof renderTagFilter==='function') renderTagFilter();        // libelles filtre par tag
  if(typeof renderProjectList==='function' && WORKSPACE) renderProjectList(); // en-tete Tags + cellules
}

// ---- config : quel clip charger ----
const _qclip = new URLSearchParams(location.search).get('clip');
let CLIP = 'data/clip';
let CLIP_NAME = null;
let CLIP_SOURCE = 'original';   // 'original' | 'corrected' : version chargee/editee
// Version du maillage du clip courant (scene.mesh_version). Sert de cache-buster
// dans l'URL /mesh_frame : URL stable par clip+version -> le cache HTTP du
// navigateur ressert les octets f16 (Cache-Control immutable) au scrub/replay,
// et l'URL change (donc se recharge) quand le clip est re-enregistre.
let MESH_VERSION = 0;
let commentsList = [];          // commentaires du clip courant (chat par clip)

const SMPL_NAMES = ["pelvis","l_hip","r_hip","spine1","l_knee","r_knee","spine2",
  "l_ankle","r_ankle","spine3","l_foot","r_foot","neck","l_collar","r_collar",
  "head","l_shoulder","r_shoulder","l_elbow","r_elbow","l_wrist","r_wrist",
  "l_hand","r_hand"];
const DCOL = [0xff6622,0x33aaff,0x33ee55,0xee44cc,0xffd722,0x9955ff,0x33ffff];

const $ = id => document.getElementById(id);
// --- toggle « Sol estimé » : bouton en haut (etat = classe .on) ---
// (remplace l'ancienne case a cocher ; helpers pour garder le code lisible)
function floorOnChecked(){ return $('floor-on').classList.contains('on'); }
function setFloorOnChecked(v){ $('floor-on').classList.toggle('on', !!v); }
function setFloorOnDisabled(v){ $('floor-on').disabled = !!v; if(v) setFloorOnChecked(false); }
let scene, camera, renderer, orbit, tcontrols, raycaster, pointer;
let DATA;
let joints;
let edited;
let N,T,J;
let dancers=[];
let bg;
let bgTex=[];
let bgSegCache=[];       // cache canvas-textures masquees par frame (ML segmentation)
let bgVersion=0;        // token anti-cache des textures du fond (POST /set_bg_offset)
let curFrame=0, playing=false;
let musicEnabled=false;      // son du clip actif (bouton 🔊/🔇) ; defaut : coupe
let selDancer=0, selJoint=0;
// ---- etirement du deplacement (points cibles du bassin) ----
// stretchPts[n] = tableau trie de {f, x, y, z} = position CIBLE du bassin (joint 0)
// du danseur n a la frame f. Quand stretchMode est actif, deplacer le danseur n
// pose/maj un point cible a la frame courante, et edited[n] est recompose =
// joints[n] + stretchOffset(n,t) pour TOUS les joints/frames (offset rigide par axe).
let stretchPts=[];             // par danseur : [] ou liste triee de points cibles
let stretchMode=false;         // mode etirement actif (toggle global)
let bgMoveMode=false;
let dancerMoveMode=true;      // gizmo au bassin quand l'accordeon Global est ouvert
let SORT_METRIC='';           // '' = A→Z (ordre liste) ; sinon nom de metrique (tri decroissant)
let FILTER_CORRECTED=false;   // picker : n'afficher que les clips deja corriges
let dancerProxy;
let proxyLastPos=new THREE.Vector3();
let dragStartPos=new THREE.Vector3();   // position du proxy/joint au DEBUT d'un drag gizmo (1 commande undo)
let draggingGizmo=false;
let stretchDragSnap=null;               // snapshot des points au debut d'un drag (mode etirement)
let meshObjs=[];
let meshLive=false;          // maillage "frame courante" actif (verts a la demande)
let meshFaces=null;          // Int32Array des faces SMPL (partagees, chargees 1x)
let meshCache=new Map();     // frame -> Float32Array (N*6890*3) ; cache LRU
const MESH_CACHE_MAX=180;    // plafond de frames gardees en cache (memoire bornee)
// cache des verts de BASE (poses d'origine, /mesh_frame) — sert au chemin
// "translation pure" : on affiche base + offset rigide SANS refit (instantane,
// pieds preserves). frame -> Float32Array (N*6890*3). LRU comme meshCache.
let baseMeshCache=new Map();
let baseMeshInflight=new Set();
// ---- fantome « avant » : maillage SMPL du motion D'ORIGINE (pre-edition),
// superpose en semi-transparent. Les verts viennent de loadBaseMeshVerts
// (/mesh_frame = poses chargees, jamais affectees par les editions live).
let ghostObjs=[];            // N THREE.Mesh ghost (faces SMPL partagees)
let ghostOn=false;           // toggle « Fantome avant » (defaut OFF)
let ghostFrameSeq=0;         // jeton anti-course (scrub rapide)
let meshFetchSeq=0;          // jeton anti-course (scrub rapide)
let meshDebounce=null;       // timer de debounce du scrub
// ---- prechargement en fenetre glissante pendant la lecture ----
const MESH_PREFETCH_AHEAD=14;   // frames a precharger devant la tete de lecture
const MESH_PREFETCH_CONC=5;     // fetchs /mesh_frame concurrents max
let meshInflight=new Set();      // frames en cours de fetch (anti-doublon)
let meshPrefetchOn=false;        // boucle de prechargement active (lecture)
// ---- mise en cache de TOUT le clip (remplissage de fond du cache HTTP) ----
const MESH_BUFFER_CONC=10;       // fetchs /mesh_frame concurrents (sature le lien)
let _bufPct=0;                   // avancement mise en cache clip (0-100)
let _bufDone=false;              // mise en cache du clip terminee
let _bufSkip=false;              // l'utilisateur a cliqué « passer » (entrer avant la fin)
let meshBufferToken=0;           // jeton anti-course : incremente a chaque (re)chargement de clip
let CLIPS=null;
let WORKSPACE=null;          // bundles .motion enregistrés (GET /workspace) ; null = pas encore chargé
// ---- liste unifiee des projets (.motion) : tri/filtre/navigation ----
let PROJ_HAS_METRICS=false;  // GET /get_config.has_metrics : colonnes metriques actives
let PROJ_SORT_KEY='name';    // colonne de tri courante (name|source_clip|has_video|has_music|mtime|<metrique>)
let PROJ_SORT_DIR=1;         // 1 = asc, -1 = desc
let PROJ_FILTER='';          // texte de recherche (nom + source_clip)
// ---- tags libres par clip (GET/POST /tags) : tri en listes/categories ----
let PROJ_TAGS={};            // { '<clip>': ['parfait','sol cassé'], ... } (GET /tags)
let PROJ_ALL_TAGS=[];        // union triee de tous les tags utilises (suggestions + filtre)
let PROJ_TAG_FILTER=new Set();// tags actifs dans le filtre : un clip passe s'il a AU MOINS un (ANY)
let PROJ_CURRENT=null;       // nom du projet actuellement charge (surlignage + nav)
let _projOrder=[];           // ordre courant (tri+filtre) des noms, pour la nav ◀ ▶
let _metricsPollTimer=null;  // polling GET /metrics_status (job metriques de fond)
let _importPollTimer=null;   // polling GET /import_status (import dossier de fond)
// ---- prechargement du fond (crop/remove-bg) en fenetre glissante, comme le maillage ----
const BG_PREFETCH_AHEAD=14;  // frames de fond a precharger devant la tete de lecture
const BG_PREFETCH_CONC=4;    // fetchs /bg_nobg concurrents max (prefetch + a la demande)
let bgPrefetchOn=false;      // boucle de prechargement du fond active (lecture)
let _prewarmPollTimer=null;  // polling GET /prewarm_status (warm-up serveur du fond)
// ---- metriques live (overlay bas-gauche) + refit auto en fin de geste ----
const METRIC_ORDER=['float','penetrate','skate','pfc','self_pen','inter_pen','jitter'];
const METRIC_DECIMALS={float:2,penetrate:2,skate:2,pfc:3,self_pen:3,inter_pen:1,jitter:2};
// les metriques arrivent du plugin sous forme {cle: nombre} avec des cles
// ARBITRAIRES. On affiche d'abord les cles connues (ordre ci-dessus), puis
// toute cle supplementaire ajoutee a la fin.
// echappe le HTML (cles de metriques arbitraires injectees en innerHTML).
function escHtml(s){
  return String(s).replace(/[&<>"']/g, c=>(
    {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
}
// libelle d'une cle de metrique : i18n si connue, sinon "humanisation" de la
// cle brute (snake_case -> "Snake case") en repli.
function metricLabel(key){
  const i18nKey='metrics.'+key;
  const lbl=t(i18nKey);
  if(lbl!==i18nKey) return lbl;       // cle connue (i18n) -> libelle traduit
  // repli : cle brute humanisee (underscores -> espaces, 1re lettre en majuscule)
  const human=String(key).replace(/[_-]+/g,' ').trim();
  return human ? human.charAt(0).toUpperCase()+human.slice(1) : key;
}
// ordre d'affichage final : cles connues presentes d'abord, puis extras.
function metricKeysToRender(){
  const seen=new Set();
  const keys=[];
  const add=k=>{ if(k!=null && !seen.has(k)){ seen.add(k); keys.push(k); } };
  for(const k of METRIC_ORDER){
    if((metricsRef&&k in metricsRef)||(metricsCur&&k in metricsCur)) add(k);
  }
  for(const src of [metricsRef, metricsCur]){
    if(src) for(const k of Object.keys(src)) add(k);
  }
  return keys;
}
let metricsRef=null;         // metriques de REFERENCE (pre-calculees, picker) {7 cles}
let metricsCur=null;         // metriques ACTUELLES (clip entier, apres « recalculer ») {7 cles}
let metricsDirty=false;      // une edition a invalide la colonne « actuel »
let metricsPanelOn=false;    // overlay metriques affiche
let liveBusy=false;          // un refit live (frame) est en cours
let liveDirty=false;         // une edition est survenue pendant un refit -> relancer
let liveTimer=null;          // debounce du refit auto apres geste
const LIVE_DEBOUNCE_MS=450;  // delai d'inactivite avant refit auto
const LIVE_WINDOW=2;         // demi-fenetre de frames refitees autour de curFrame (skate/jitter)
const LIVE_ITERS=80;         // iters du refit live (compromis vitesse/precision)
let metricsClipBusy=false;   // recalcul "tout le clip" en cours
let floorGrid=null;          // sol estime (grille inclinee)
let shadowFloor=null;        // capteur d'ombre au sol (plan horizontal, ombres seules)
let floorPlane=null;         // [a,b,c] du sol ACTUELLEMENT affiche (variante courante / edition)
let floorVariant='corrected';// variante de sol affichee (corrected/raw/manual)
let floorEditMode=false;     // mode « Corriger le sol » actif (gizmo sur le damier)
let _accLock=false;          // garde re-entrance accordeon (declare tot : evite TDZ)
// etat sauvegarde/export (cartouche en haut) : declare tot car teardownScene y
// touche au chargement d'un clip -> evite la TDZ (let hoisting).
let saveDirty=false;         // editions non sauvegardees depuis le dernier /save_pkl
let saveBusy=false;          // /save_pkl en cours
let saveDoneThisSession=false; // une vraie sauvegarde a eu lieu sur ce clip (sinon : pas de pastille verte « Enregistré »)
let _skipDraftRestore=false;   // saute la restauration de brouillon (chargement d'un bundle .motion)
let exportBusy=false;        // /export_pkl (telechargement) en cours
// onglets valides (declare tot : setTab() tourne dans bindTabs au demarrage)
const TAB_NAMES=['clip','edit','floor','video','comments'];

function idx(n,t,j){ return ((n*T + t)*J + j)*3; }

// Controles d'edition/affichage qui n'ont de sens QU'AVEC un clip ouvert. On les
// desactive a vide (etat d'accueil) pour que l'UI ne propose pas d'actions vouees
// a l'echec ; ils sont reactives a l'ouverture d'un clip (gateControls()).
// Declare avant init() pour eviter toute zone morte temporelle (TDZ).
const GATED_CTRL_IDS=[
  // onglet Edition
  'sel-d','sel-j','move-all','g-x-minus','g-x-plus','g-z-minus','g-z-plus',
  'g-y-minus','g-y-plus','g-step','g-reset','stretch-mode','stretch-anchor',
  'stretch-setpt','stretch-delpt','stretch-clearpts','j-x','j-y','j-z','reset-j',
  'refit-cur','refit-all','correct-input-raw','correct-input-edited','correct-motion',
  // onglet Sol
  'floor-variant','floor-edit','floor-recompute',
  // onglet Video
  'bg-on','bg-move','bg-x','bg-y','bg-z','bg-s','bg-o','bg-remove',
  'bg-import-video-file','bg-import-video','bg-import-music-file','bg-import-music',
  // toggles scene + export (la pastille Save est geree par renderSavePill)
  't-mesh','t-ghost','floor-on','floor-dist','export-pkl',
];

// ====================================================================
//  Undo / Redo : commandes inversibles (2 piles)
// ====================================================================
const UNDO_MAX=100;
let undoStack=[], redoStack=[];
function pushCmd(cmd){
  undoStack.push(cmd);
  if(undoStack.length>UNDO_MAX) undoStack.shift();
  redoStack.length=0;
  refreshUndoButtons();
  if(typeof markDirty==='function') markDirty();           // cartouche « non sauvegardé »
  if(typeof scheduleLive==='function') scheduleLive();   // refit SMPL + metriques auto
}
// applique un delta (sens=+1 pour redo, -1 pour undo) a une commande
function applyCmd(cmd, sign){
  if(cmd.type==='move'){
    const n=cmd.n;
    const frames = cmd.allFrames ? Array.from({length:T},(_,k)=>k) : cmd.frames;
    for(const tt of frames){ for(let jj=0;jj<J;jj++){ const b=idx(n,tt,jj);
      edited[b]+=sign*cmd.dx; edited[b+1]+=sign*cmd.dy; edited[b+2]+=sign*cmd.dz; } }
    // garde le cumul d'offset constant du danseur n coherent avec undo/redo
    if(!stepCum[n]) stepCum[n]={x:0,y:0,z:0};
    stepCum[n].x+=sign*cmd.dx; stepCum[n].y+=sign*cmd.dy; stepCum[n].z+=sign*cmd.dz;
  } else if(cmd.type==='joint'){
    const v = (sign>0)? cmd.after : cmd.before;
    const b=idx(cmd.n,cmd.t,cmd.j);
    edited[b]=v[0]; edited[b+1]=v[1]; edited[b+2]=v[2];
  } else if(cmd.type==='stretch'){
    // restaure les points du danseur (before pour undo, after pour redo) puis recompose
    stretchRestore(cmd.n, (sign>0)? cmd.after : cmd.before);
    recomposeDancer(cmd.n);
  } else if(cmd.type==='snapshot'){
    // instantane complet de `edited` (avant/apres) : sert aux operations massives
    // (correction auto) pour rester reversibles en une seule entree d'historique.
    const src=(sign>0)? cmd.after : cmd.before;
    edited.set(src);
    for(let n=0;n<N;n++){ stretchPts[n]=[]; }
    if(typeof resetStepperVals==='function') resetStepperVals();
  }
}
function undo(){
  if(!undoStack.length) return;
  const cmd=undoStack.pop(); applyCmd(cmd,-1); redoStack.push(cmd);
  if(cmd.type==='move'||cmd.type==='stretch'){ selDancer=cmd.n; $('sel-d').value=cmd.n; }
  else if(cmd.type==='joint'){ selDancer=cmd.n; selJoint=cmd.j; $('sel-d').value=cmd.n; $('sel-j').value=cmd.j; }
  if(typeof syncGlobalFields==='function') syncGlobalFields();
  setFrame(curFrame); refreshUndoButtons(); if(typeof renderStretchPanel==='function') renderStretchPanel();
  if(typeof markDirty==='function') markDirty();
  if(typeof scheduleLive==='function') scheduleLive();
}
function redo(){
  if(!redoStack.length) return;
  const cmd=redoStack.pop(); applyCmd(cmd,+1); undoStack.push(cmd);
  if(cmd.type==='move'||cmd.type==='stretch'){ selDancer=cmd.n; $('sel-d').value=cmd.n; }
  else if(cmd.type==='joint'){ selDancer=cmd.n; selJoint=cmd.j; $('sel-d').value=cmd.n; $('sel-j').value=cmd.j; }
  if(typeof syncGlobalFields==='function') syncGlobalFields();
  setFrame(curFrame); refreshUndoButtons(); if(typeof renderStretchPanel==='function') renderStretchPanel();
  if(typeof markDirty==='function') markDirty();
  if(typeof scheduleLive==='function') scheduleLive();
}
function refreshUndoButtons(){
  $('undo').disabled = !undoStack.length;
  $('redo').disabled = !redoStack.length;
}


async function init(){
  scene = new THREE.Scene();
  scene.background = new THREE.Color(0x1b1d22);
  const view = $('view');
  camera = new THREE.PerspectiveCamera(45, view.clientWidth/view.clientHeight, 0.01, 100);
  camera.up.set(0,0,1);
  renderer = new THREE.WebGLRenderer({antialias:true});
  renderer.setSize(view.clientWidth, view.clientHeight);
  renderer.setPixelRatio(window.devicePixelRatio);
  renderer.shadowMap.enabled=true;
  renderer.shadowMap.type=THREE.PCFSoftShadowMap;
  view.appendChild(renderer.domElement);

  orbit = new OrbitControls(camera, renderer.domElement);
  orbit.enableDamping = true;

  // eclairage volumetrique : ambiante douce + hemisphere (ciel/sol) + directionnelle
  // en hauteur (monde z-up) qui projette les ombres des SMPL au sol.
  scene.add(new THREE.AmbientLight(0xffffff,0.45));
  scene.add(new THREE.HemisphereLight(0xbfd4ff, 0x3a3a30, 0.55));
  const dl = new THREE.DirectionalLight(0xffffff,1.15);
  dl.position.set(3,-4,9);
  dl.target.position.set(0,0,0);
  dl.castShadow=true;
  dl.shadow.camera.left=-4; dl.shadow.camera.right=4;
  dl.shadow.camera.top=4;   dl.shadow.camera.bottom=-4;
  dl.shadow.camera.near=0.5; dl.shadow.camera.far=40;
  dl.shadow.mapSize.set(2048,2048);
  dl.shadow.bias=-0.0005; dl.shadow.normalBias=0.02;
  scene.add(dl); scene.add(dl.target);

  raycaster = new THREE.Raycaster(); pointer = new THREE.Vector2();

  tcontrols = new TransformControls(camera, renderer.domElement);
  tcontrols.setSize(0.7);
  tcontrols.addEventListener('dragging-changed', onDraggingChanged);
  tcontrols.addEventListener('objectChange', onGizmoMove);
  scene.add(tcontrols);

  dancerProxy = new THREE.Object3D();
  scene.add(dancerProxy);

  bindUI();
  bindPicker();
  bindTabs();
  bindComments();
  bindStage2Features();
  bindMenubar();
  applyLang(LANG);
  resize(); window.addEventListener('resize', resize);
  animate();

  // config (has_metrics + dossiers) + liste des projets + job metriques de fond.
  await loadProjectConfig();
  refreshProjects(true).then(()=>{ pollMetricsStatus(); });

  if(_qclip && _qclip.startsWith('data/')){
    await loadClipByPath(_qclip);
  } else if(_qclip){
    await loadClipByName(_qclip);
  } else {
    $('status').textContent = t('msg.pickClip');
    setTab('clip');
    // Editeur vide au demarrage : ecran d'accueil centre dans #view (parcourir /
    // ouvrir un dossier / importer un .pkl) ; barre de lecture masquee.
    renderEmptyState();
  }
}

async function loadClipByPath(path){
  showOverlay(tf('js.load.overlay',{name:path}));
  try{
    const r = await fetch(`${path}/scene.json`);
    if(!r.ok) throw new Error(`scene.json introuvable (${r.status}) à ${path}`);
    const data = await r.json();
    CLIP = path; CLIP_NAME = data.name || null;
    CLIP_SOURCE = data.source || 'original';
    MESH_VERSION = data.mesh_version || 0;   // cache-buster /mesh_frame (immutable)
    teardownScene();
    DATA = data;
    buildFromData();
    $('status').style.color='#7fd18b';
    $('status').textContent = `✓ ${DATA.name} — ${N} ${t('msg.dancers')}, ${T} ${t('msg.frames')}`;
    updateClipInfo();
    setTab('edit');
    await afterClipLoaded();
    await warmFirstFrame();
  }catch(err){
    $('status').textContent = '✗ ' + err.message; $('status').style.color = '#ff7777';
  }finally{ hideOverlay(); }
}

async function loadClipByName(name, source){
  source = ['corrected','custom','custom_corrected'].includes(source) ? source : 'original';
  showOverlay(tf('js.load.overlay',{name}));
  try{
    const r = await fetch(`/load?clip=${encodeURIComponent(name)}&source=${source}`);
    if(!r.ok) throw new Error("/load — "+await errMsg(r));
    const data = await r.json();
    CLIP = data._clip_dir || `data/${name}`;
    CLIP_NAME = name;
    CLIP_SOURCE = data.source || source;
    MESH_VERSION = data.mesh_version || 0;   // cache-buster /mesh_frame (immutable)
    teardownScene();
    DATA = data;
    buildFromData();
    $('status').style.color='#7fd18b';
    $('status').textContent = `✓ ${DATA.name} — ${N} ${t('msg.dancers')}, ${T} ${t('msg.frames')}`+
      (CLIP_SOURCE==='corrected'?' · '+t('source.editing.corrected'):'')+
      (DATA.has_video===false||!(DATA.frames&&DATA.frames.length)?t('msg.novideo'):'');
    updateClipInfo();
    setTab('edit');
    pushRecent(CLIP_NAME, 'clip', CLIP_SOURCE);   // fichiers récents (écran d'accueil)
    // UNE seule surcouche : on la garde jusqu'à ce que la 1re frame soit prête
    // (mailles construites + 1er fond si affiché). La lecture démarre ensuite à chaud.
    await afterClipLoaded();
    await warmFirstFrame();
  }catch(err){
    $('status').textContent = '✗ ' + err.message; $('status').style.color = '#ff7777';
  }finally{ hideOverlay(); }
}

// reference metriques du clip (pre-calculees) depuis le cache /clips, sinon null.
function findRefMetrics(name){
  if(!CLIPS) return null;
  const c=CLIPS.find(x=>x.name===name);
  return (c && c.metrics && Object.keys(c.metrics).length) ? c.metrics : null;
}

// metriques de DEPART portees directement par la scene chargee (/load et
// /bundle/load renvoient scene.metrics = {ref:{...}, cur:{...}}). Robuste a la
// forme plate (anciens backends). null si absentes -> on retombe sur /clips.
function sceneRefMetrics(){
  const m=DATA && DATA.metrics;
  if(!m || typeof m!=='object') return null;
  let ref=null;
  if(m.ref && typeof m.ref==='object') ref=m.ref;       // forme {ref, cur}
  else if(!m.cur && !m.ref) ref=m;                       // forme plate
  return (ref && Object.keys(ref).length) ? ref : null;
}

// apres chargement d'un clip : maillage live ON par defaut + overlay metriques
// (reference = pre-calculee) affiche, pret a refleter les editions.
async function afterClipLoaded(){
  renderEmptyState();   // un clip est ouvert -> retire l'ecran d'accueil + montre la barre
  gateControls();       // clip ouvert -> reactive les controles d'edition/affichage
  loadComments();
  // DEPART = metriques d'origine du clip, montrees AUTOMATIQUEMENT (sans clic).
  // Priorite a scene.metrics.ref (porte par /load et /bundle/load) ; sinon le
  // cache /clips ; sinon null (chargement de fond ci-dessous).
  setMetricsRef(sceneRefMetrics() || findRefMetrics(CLIP_NAME));
  showMetricsPanel(false);   // mode live OFF par defaut : edition instantanee. Le toggle « Maillage » l'active.
  setMetricsStatus(t('metrics.waiting'), '#9aa0ac');
  // si la reference n'est pas encore connue (ni scene ni cache /clips), on charge
  // /clips en tache de fond puis on remplit la colonne "depart".
  if(metricsRef==null && CLIP_NAME){
    fetch('/clips').then(r=>r.ok?r.json():null).then(j=>{
      if(j){ CLIPS=j.clips; if(metricsRef==null){ setMetricsRef(findRefMetrics(CLIP_NAME)); } }
    }).catch(()=>{});
  }
  // préférence "squelette par défaut" (réglages) : OFF -> on masque le squelette.
  if(!sceneDefault('skel', true) && dancers.length){
    dancers.forEach(d=>{d.spheres.forEach(s=>s.visible=false);d.bones.visible=false;});
    $('t-skel').classList.remove('on');
  }
  // préférence "sol estimé par défaut" (réglages) : ON -> affiche le damier.
  if(sceneDefault('floor', false) && !$('floor-on').disabled){
    setFloorOnChecked(true); if(typeof floorGrid!=='undefined' && floorGrid) floorGrid.visible=true;
  }
  // maillage active par defaut a l'ouverture d'un clip (mode live + panneau
  // metriques). Respecte la préférence "maillage par défaut" (réglages).
  if(CLIP_NAME && !meshObjs.length && sceneDefault('mesh', true)){
    $('t-mesh').classList.add('on');
    try{ const ok=await enableLiveMesh(); if(!ok) $('t-mesh').classList.remove('on'); }
    catch(_){ $('t-mesh').classList.remove('on'); }
  }
  // si le remove-bg est deja actif (ex : rechargement), amorce le warm serveur du
  // fond pour eviter le gel par frame. No-op si remove-bg est off (cas par defaut).
  if(bgRemoveActive()) prewarmBg();
  syncFloorDistAvail();   // le maillage vient (peut-etre) de s'activer -> degrise « Distance au sol »
  // filet local : restaure un brouillon d'édits si présent pour ce clip+source.
  // (pas pour les bundles .motion : ils portent déjà leurs édits enregistrés.)
  if(!_skipDraftRestore && typeof maybeRestoreDraft==='function') maybeRestoreDraft();
  _skipDraftRestore=false;
  // La mise en cache de TOUT le clip est lancée et ATTENDUE par warmFirstFrame()
  // (voile maintenu jusqu'à 100% ou « passer »), pas ici.
}

function updateClipInfo(){
  const v = (DATA.frames&&DATA.frames.length)?t('video.with'):t('video.without');
  const txt = `${DATA.name} · ${N}×${T} · ${v}`;
  $('clip-info').textContent = txt;
  if($('clip-info-full')) $('clip-info-full').innerHTML =
    `<b>${DATA.name}</b><br>${N} ${t('msg.dancers')} · ${T} ${t('msg.frames')} · ${DATA.fps||30} fps<br>${v}`;
}

function teardownScene(){
  tcontrols.detach();
  for(const d of dancers){
    d.spheres.forEach(s=>{ scene.remove(s); s.geometry?.dispose?.(); s.material?.dispose?.(); });
    scene.remove(d.bones); d.bones.geometry?.dispose?.(); d.bones.material?.dispose?.();
  }
  dancers=[];
  for(const m of meshObjs){ scene.remove(m); m.geometry?.dispose?.(); m.material?.dispose?.(); }
  meshObjs=[];
  // fantome « avant » : dispose + reset du toggle au changement de clip
  disposeGhost(); ghostOn=false; ghostFrameSeq++;
  if($('t-ghost')) $('t-ghost').classList.remove('on');
  meshLive=false; meshFaces=null; meshCache.clear();
  baseMeshCache.clear(); baseMeshInflight.clear();
  meshPrefetchOn=false; meshInflight.clear();
  meshBufferToken++;                 // annule la mise en cache de fond du clip precedent
  if(typeof setBufferStatus==='function') setBufferStatus(null);
  meshFetchSeq++; if(meshDebounce){ clearTimeout(meshDebounce); meshDebounce=null; }
  // metriques live : on remet a zero (la reference est re-renseignee a l'ouverture)
  if(liveTimer){ clearTimeout(liveTimer); liveTimer=null; }
  liveBusy=false; liveDirty=false; metricsRef=null; metricsCur=null; metricsDirty=false;
  showMetricsPanel(false); renderMetricsPanel();
  // nouveau clip = aucune edition ET aucune sauvegarde encore faite cette session
  saveDirty=false; saveBusy=false; saveDoneThisSession=false;
  if(typeof renderSavePill==='function') renderSavePill();
  $('t-mesh').classList.remove('on');
  if(bg){ scene.remove(bg); bg.geometry?.dispose?.(); bg.material?.dispose?.(); bg=null; }
  for(const tx of bgTex){ tx?.dispose?.(); }
  for(const tx of bgSegCache){ tx?.dispose?.(); }
  bgTex=[]; bgSegCache=[]; bgVersion=0;
  // nouveau clip : on retente la segmentation serveur (peut reussir meme si un
  // clip precedent avait echoue) et on vide la file de fetch en cours.
  _serverNoBgFailed=false; _serverNoBgPending=new Set();
  if($('bg-t-status')) $('bg-t-status').textContent='';
  // sort du mode correction du sol AVANT de detruire le damier
  if(floorEditMode){ floorEditMode=false; $('floor-edit').classList.remove('on');
    ['floor-tx','floor-ty','floor-h','floor-reset','floor-save'].forEach(id=>{ const e=$(id); if(e) e.disabled=true; }); }
  removeFloor();
  removeShadowFloor();
  removeFloorDistLines(); floorDistOn=false;
  if($('floor-dist')){ $('floor-dist').classList.remove('on'); $('floor-dist').disabled=true; }
  floorPlane=null; floorVariant='corrected';
  if($('floor-save-status')) $('floor-save-status').textContent='';
  if($('floor-recompute-status')) $('floor-recompute-status').textContent='';
  // coupe et detache la musique du clip precedent
  const _au=$('music'); if(_au){ _au.pause(); _au.removeAttribute('src'); _au.load(); }
  if($('music-toggle')){ $('music-toggle').disabled=true; }
  $('sel-d').innerHTML=''; $('sel-j').innerHTML='';
  curFrame=0; playing=false; selDancer=0; selJoint=0;
  // reset etirement (mode + points) au changement de clip
  stretchPts=[]; stretchMode=false; stretchDragSnap=null;
  if($('stretch-mode')) $('stretch-mode').checked=false;
  if($('stretch-box')) $('stretch-box').hidden=true;
  if($('stretch-frieze')) $('stretch-frieze').innerHTML='';
  if($('stretch-curoff')) $('stretch-curoff').textContent='';
  bgMoveMode=false;
  $('bg-move').classList.remove('on');
  $('refit-status').textContent=''; $('save-status').textContent='';
  undoStack.length=0; redoStack.length=0; refreshUndoButtons();
  resetStepperVals();
  if(DATA){ DATA._verts=null; }
}

function showOverlay(msg){ $('overlay-msg').textContent=msg; $('overlay').classList.add('show'); $('overlay').removeAttribute('aria-hidden'); }
function hideOverlay(){ $('overlay').classList.remove('show'); $('overlay').setAttribute('aria-hidden','true'); }

// Extrait un message d'erreur LISIBLE d'une reponse HTTP en echec : on prefere le
// champ {error} du JSON renvoye par le serveur ; a defaut un court extrait texte ;
// en dernier recours juste le code HTTP. Evite d'exposer le JSON/HTML brut a l'UI.
async function errMsg(resp){
  let txt='';
  try{ txt=await resp.text(); }catch(_){}
  if(txt){
    try{ const j=JSON.parse(txt); if(j && j.error) return String(j.error); }catch(_){}
    const clean=txt.trim();
    // texte non-JSON court (pas une page HTML) : on l'affiche tel quel.
    if(clean && clean[0]!=='<' && clean.length<=200) return clean;
  }
  return `HTTP ${resp.status}`;
}

// Toast visible (haut-centre), auto-disparition. kind : 'err' (defaut) | 'ok' | 'info'.
// Sert a remonter une action refusee ou une erreur sans la cacher dans un #*-status.
let _toastTimer=null;
function toast(msg, kind){
  let el=$('toast');
  if(!el){
    el=document.createElement('div');
    el.id='toast'; el.setAttribute('role','status'); el.setAttribute('aria-live','polite');
    document.body.appendChild(el);
  }
  el.className=''; el.classList.add('show', 'toast-'+(kind||'err'));
  el.textContent=msg;
  if(_toastTimer) clearTimeout(_toastTimer);
  _toastTimer=setTimeout(()=>{ el.classList.remove('show'); }, 4200);
}

// Dialogue de confirmation modal accessible (reutilise openModal/closeModal :
// focus piege, Echap = annuler). Resout true (OK) / false (annuler/Echap).
function confirmDialog(title, body, okLabel, cancelLabel){
  return new Promise(resolve=>{
    let dlg=$('confirm-dialog');
    if(!dlg){
      dlg=document.createElement('div');
      dlg.id='confirm-dialog';
      dlg.setAttribute('role','dialog');
      dlg.setAttribute('aria-modal','true');
      dlg.setAttribute('aria-labelledby','confirm-title');
      dlg.setAttribute('aria-hidden','true');
      dlg.innerHTML=
        `<div id="confirm-box">`+
        `<h3 id="confirm-title"></h3>`+
        `<div id="confirm-body" class="small"></div>`+
        `<div id="confirm-actions">`+
        `<button type="button" id="confirm-cancel"></button>`+
        `<button type="button" id="confirm-ok"></button>`+
        `</div></div>`;
      document.body.appendChild(dlg);
    }
    $('confirm-title').textContent=title;
    $('confirm-body').textContent=body;
    $('confirm-ok').textContent=okLabel||t('confirm.ok');
    $('confirm-cancel').textContent=cancelLabel||t('confirm.cancel');
    const done=val=>{ closeModal(dlg); $('confirm-ok').onclick=null; $('confirm-cancel').onclick=null;
      dlg._onEsc=null; resolve(val); };
    $('confirm-ok').onclick=()=>done(true);
    $('confirm-cancel').onclick=()=>done(false);
    // Echap (gere par le handler global des modales) -> closeModal sans resoudre :
    // on branche un hook pour resoudre false dans ce cas.
    dlg._onEsc=()=>done(false);
    openModal(dlg, document.activeElement, $('confirm-cancel'));
  });
}

// ---- ecran d'accueil (premier lancement, aucun clip ouvert) ----
// Affiche un etat vide centre dans #view avec 3 actions (parcourir / ouvrir un
// dossier / importer un .pkl) et masque la barre de lecture tant qu'aucun clip
// n'existe. Appele au demarrage (pas de clip), au teardown, et a chaque
// changement de langue (re-traduction). Retire des qu'un clip est charge.
function renderEmptyState(){
  const view=$('view'); if(!view) return;
  const bar=$('bar');
  if(DATA){
    // un clip est ouvert : retire l'ecran d'accueil + reaffiche la barre de lecture
    const es=$('empty-state'); if(es) es.remove();
    if(bar) bar.hidden=false;
    return;
  }
  // pas de clip : barre de lecture masquee
  if(bar) bar.hidden=true;
  let es=$('empty-state');
  if(!es){
    es=document.createElement('div');
    es.id='empty-state';
    es.innerHTML=
      `<div class="es-title"></div><div class="es-sub"></div>`+
      `<div class="es-actions">`+
      `<button type="button" class="es-btn primary" id="es-browse">`+
        `<span class="es-btn-main"></span><span class="es-btn-sub"></span></button>`+
      `<button type="button" class="es-btn" id="es-folder">`+
        `<span class="es-btn-main"></span><span class="es-btn-sub"></span></button>`+
      `<button type="button" class="es-btn" id="es-import">`+
        `<span class="es-btn-main"></span><span class="es-btn-sub"></span></button>`+
      `</div>`;
    view.appendChild(es);
    es.querySelector('#es-browse').onclick=()=>openPicker();         // charger un projet
    es.querySelector('#es-folder').onclick=()=>openFolderDialog();   // charger un dossier
    es.querySelector('#es-import').onclick=()=>openPklPicker();      // charger un fichier (.pkl)
  }
  // (re)traduit les libelles (appele aussi depuis applyLang)
  es.querySelector('.es-title').textContent=t('empty.title');
  es.querySelector('.es-sub').textContent=t('empty.sub');
  const set=(id,main,sub)=>{
    const b=es.querySelector(id); if(!b) return;
    b.querySelector('.es-btn-main').textContent=t(main);
    b.querySelector('.es-btn-sub').textContent=t(sub);
  };
  set('#es-browse','empty.browse','empty.browse.sub');
  set('#es-folder','empty.folder','empty.folder.sub');
  set('#es-import','empty.import','empty.import.sub');
  renderRecentFiles(es);   // fichiers récents (localStorage) en bas de l'écran d'accueil
  // pas de clip -> grise les controles d'edition/affichage (et la pastille Save).
  gateControls();
}

// ====================================================================
//  Stage 2 — réglages, aide raccourcis, autosave, fichiers récents, /info
// --------------------------------------------------------------------
//  Toutes ces fonctionnalités sont "frontend-only" et persistées dans
//  localStorage (préfixe `pe.`). Elles s'appuient sur le système i18n et
//  les helpers de modale existants (openModal/closeModal : focus piégé).
// ====================================================================

// ---- fichiers récents (bundles/clips ouverts) ----
const RECENT_KEY='pe.recent';
const RECENT_MAX=6;
function getRecent(){
  try{ const a=JSON.parse(localStorage.getItem(RECENT_KEY)||'[]'); return Array.isArray(a)?a:[]; }
  catch(_){ return []; }
}
// Mémorise un clip/bundle fraîchement ouvert en tête de la liste récente.
// kind: 'clip' | 'bundle' ; source: original/corrected/… (pour ré-ouvrir pareil).
function pushRecent(name, kind, source){
  if(!name) return;
  let a=getRecent().filter(r=>!(r.name===name && r.kind===kind));
  a.unshift({name, kind:kind||'clip', source:source||'original', ts:Date.now()});
  if(a.length>RECENT_MAX) a=a.slice(0,RECENT_MAX);
  try{ localStorage.setItem(RECENT_KEY, JSON.stringify(a)); }catch(_){}
}
// (Re)construit la liste des fichiers récents dans l'écran d'accueil `es`.
function renderRecentFiles(es){
  if(!es) return;
  let box=es.querySelector('.es-recent');
  const recent=getRecent();
  if(!recent.length){ if(box) box.remove(); return; }
  if(!box){
    box=document.createElement('div');
    box.className='es-recent';
    box.innerHTML='<div class="es-recent-title"></div><div class="es-recent-list"></div>';
    es.appendChild(box);
  }
  box.querySelector('.es-recent-title').textContent=t('recent.title');
  const list=box.querySelector('.es-recent-list');
  list.innerHTML='';
  recent.forEach(r=>{
    const item=document.createElement('button');
    item.type='button'; item.className='es-recent-item';
    const tag=(r.kind==='bundle')?t('tag.bundle')
      :(r.source==='corrected'?t('tag.corrected'):'');
    item.innerHTML=`<span class="nm"></span><span class="es-recent-tag"></span>`;
    item.querySelector('.nm').textContent=r.name;
    item.querySelector('.es-recent-tag').textContent=tag;
    item.onclick=()=>{
      if(r.kind==='bundle') loadBundleByName(r.name);
      else loadClipByName(r.name, r.source);
    };
    list.appendChild(item);
  });
}

// ---- panneau réglages (roue ⚙) : prefs persistées dans localStorage ----
// Les toggles "scène par défaut" pilotent l'état appliqué à l'ouverture d'un
// clip ; ils reflètent/écrivent pe.def.skel / pe.def.mesh / pe.def.floor.
const SCENE_DEF_KEYS={skel:'pe.def.skel', mesh:'pe.def.mesh', floor:'pe.def.floor'};
function sceneDefault(which, fallback){
  const v=localStorage.getItem(SCENE_DEF_KEYS[which]);
  if(v===null) return fallback;
  return v==='1';
}
let _settingsOpen=false;
function openSettings(){
  const pop=$('settings-pop'), btn=$('menu-settings-btn'); if(!pop) return;
  // synchronise les contrôles avec l'état LIVE courant de la scène : les cases
  // pilotent désormais la visibilité en direct, donc elles doivent refléter la
  // réalité (état .on des boutons cachés) plutôt que le seul défaut persisté.
  if($('set-lang')) $('set-lang').value=LANG;
  const bSkel=$('t-skel'), bMesh=$('t-mesh'), bFloor=$('floor-on');
  if($('set-skel')) $('set-skel').checked=bSkel?bSkel.classList.contains('on'):sceneDefault('skel', true);
  if($('set-mesh')) $('set-mesh').checked=bMesh?bMesh.classList.contains('on'):sceneDefault('mesh', true);
  if($('set-floor')) $('set-floor').checked=bFloor?bFloor.classList.contains('on'):sceneDefault('floor', false);
  // (les champs « Dossiers source » sont pré-remplis par loadProjectConfig() au boot)
  pop.classList.add('show'); pop.removeAttribute('aria-hidden');
  if(btn) btn.setAttribute('aria-expanded','true');
  _settingsOpen=true;
  renderPluginInfo();   // rafraîchit le pied "plugins actifs" dans le panneau
}
function closeSettings(){
  const pop=$('settings-pop'), btn=$('menu-settings-btn'); if(!pop) return;
  pop.classList.remove('show'); pop.setAttribute('aria-hidden','true');
  if(btn) btn.setAttribute('aria-expanded','false');
  _settingsOpen=false;
}
function toggleSettings(){ _settingsOpen?closeSettings():openSettings(); }

// ---- aide raccourcis clavier (touche « ? ») : modale accessible ----
function openShortcuts(){
  const dlg=$('shortcuts-dialog'); if(!dlg) return;
  if(_modalStack.includes(dlg)) return;   // déjà ouverte
  openModal(dlg, document.activeElement, $('shortcuts-close'));
}
function closeShortcuts(){ const dlg=$('shortcuts-dialog'); if(dlg) closeModal(dlg); }

// ---- plugins actifs (corrector / metrics) via GET /info ----
var _serverInfo=null;  // var: hoisted, read by renderPluginInfo() during early applyLang() before this line runs
async function fetchServerInfo(){
  try{
    const r=await fetch('/info');
    if(!r.ok) return null;
    _serverInfo=await r.json();
  }catch(_){ _serverInfo=null; }
  return _serverInfo;
}
// "module:Class" -> "Class" (nom court lisible) ; null/'' -> i18n (aucun).
function _pluginShort(spec){
  if(!spec) return t('plugin.none');
  const s=String(spec);
  const colon=s.lastIndexOf(':');
  const right=colon>=0?s.slice(colon+1):s;
  const dot=right.lastIndexOf('.');
  return dot>=0?right.slice(dot+1):right;
}
// Affiche les plugins actifs : pied discret (#plugin-footer) + bas du panneau réglages.
function renderPluginInfo(){
  const corr=_serverInfo?_pluginShort(_serverInfo.corrector_spec):t('plugin.none');
  const met =_serverInfo?_pluginShort(_serverInfo.metrics_spec):t('plugin.none');
  const foot=$('plugin-footer');
  if(foot){
    foot.textContent=tf('plugin.footer',{corr, met});
    foot.classList.toggle('show', !!_serverInfo);
  }
  const sp=$('settings-plugins');
  if(sp){
    sp.innerHTML=`${escHtml(t('plugin.corrector'))}: <code>${escHtml(corr)}</code><br>`+
      `${escHtml(t('plugin.metrics'))}: <code>${escHtml(met)}</code>`+
      (_serverInfo&&_serverInfo.version?`<br>v<code>${escHtml(_serverInfo.version)}</code>`:'');
  }
}

// ---- autosave (brouillon de session) + garde "modifs non enregistrées" ----
// On persiste un brouillon léger des édits courants dans localStorage, débounced.
// Ce n'est PAS le .motion serveur : c'est un filet local pour ne pas perdre une
// session sur un rechargement accidentel. La clé est par clip+source.
const AUTOSAVE_KEY='pe.draft';
const AUTOSAVE_DEBOUNCE=1200;
let _autosaveTimer=null;
function _draftKey(){ return CLIP_NAME?`${AUTOSAVE_KEY}.${CLIP_NAME}.${CLIP_SOURCE}`:null; }
function scheduleAutosave(){
  if(_autosaveTimer) clearTimeout(_autosaveTimer);
  _autosaveTimer=setTimeout(writeDraft, AUTOSAVE_DEBOUNCE);
}
function writeDraft(){
  const key=_draftKey();
  if(!key || !edited || !saveDirty) return;
  try{
    localStorage.setItem(key, JSON.stringify({
      name:CLIP_NAME, source:CLIP_SOURCE, N, T, J,
      edited:Array.from(edited), ts:Date.now(),
    }));
  }catch(_){ /* quota plein : on abandonne silencieusement le brouillon */ }
}
function clearDraft(){
  const key=_draftKey();
  if(key){ try{ localStorage.removeItem(key); }catch(_){} }
}
// Restaure un brouillon local s'il correspond exactement au clip courant.
// Appelé après le chargement d'un clip (édits non encore appliqués).
function maybeRestoreDraft(){
  const key=_draftKey();
  if(!key || !edited) return;
  let d=null;
  try{ d=JSON.parse(localStorage.getItem(key)||'null'); }catch(_){ d=null; }
  if(!d || !Array.isArray(d.edited)) return;
  if(d.N!==N || d.T!==T || d.J!==J || d.edited.length!==edited.length) return;
  edited.set(d.edited);
  setFrame(curFrame);
  markDirty();
  if(typeof toast==='function') toast(t('autosave.restored'), 'info');
}

function bindStage2Features(){
  // « Paramètres » : l'ouverture du dialogue est branchée dans bindMenubar()
  // (le bouton #menu-settings-btn n'a pas de dropdown -> appelle toggleSettings).
  // bouton close du dialogue réglages
  const scl=$('settings-pop-close'); if(scl) scl.onclick=closeSettings;
  // « Raccourcis clavier » (#help-btn) et « Version / À propos » (#about-btn) sont
  // branchés dans bindMenubar() (après le binding générique des items de menu).
  const sclose=$('shortcuts-close'); if(sclose) sclose.onclick=closeShortcuts;
  const aclose=$('about-close'); if(aclose) aclose.onclick=closeAbout;
  // clic sur le fond de la boîte « À propos » (hors de la boîte) -> ferme
  const adlg=$('about-dialog');
  if(adlg) adlg.addEventListener('pointerdown', e=>{ if(e.target===adlg) closeAbout(); });
  // langue (réglages) : réutilise applyLang
  if($('set-lang')) $('set-lang').onchange=e=>applyLang(e.target.value);
  // toggles scène (popover ⚙) : persistent le défaut ET pilotent l'état LIVE.
  // Les vrais boutons #t-skel/#t-mesh/#floor-on sont cachés dans la barre mais
  // restent dans le DOM ; on réutilise leur logique onclick pour basculer.
  if($('set-skel')) $('set-skel').onchange=e=>{
    localStorage.setItem(SCENE_DEF_KEYS.skel, e.target.checked?'1':'0');
    const b=$('t-skel');
    if(b && b.classList.contains('on')!==e.target.checked) b.onclick();
  };
  if($('set-mesh')) $('set-mesh').onchange=e=>{
    localStorage.setItem(SCENE_DEF_KEYS.mesh, e.target.checked?'1':'0');
    const b=$('t-mesh');
    if(b && b.classList.contains('on')!==e.target.checked) b.onclick();
  };
  if($('set-floor')) $('set-floor').onchange=e=>{
    localStorage.setItem(SCENE_DEF_KEYS.floor, e.target.checked?'1':'0');
    const b=$('floor-on');
    // #floor-on peut être désactivé (pas de sol) : on persiste seulement.
    if(b && !b.disabled && b.classList.contains('on')!==e.target.checked) b.onclick();
  };
  // clic sur le fond du dialogue réglages (hors de la boîte) -> ferme
  const spop=$('settings-pop');
  if(spop) spop.addEventListener('pointerdown', e=>{ if(e.target===spop) closeSettings(); });
  // Échap ferme aussi le popover réglages (il n'est pas dans la pile modale).
  document.addEventListener('keydown', e=>{
    if(e.key==='Escape' && _settingsOpen && !_modalStack.length){ closeSettings(); }
  });
  // garde "modifs non enregistrées" : avertit avant fermeture/rechargement.
  window.addEventListener('beforeunload', e=>{
    if(saveDirty){ e.preventDefault(); e.returnValue=t('unsaved.guard'); return e.returnValue; }
  });
  // plugins actifs : charge GET /info en tâche de fond puis affiche.
  fetchServerInfo().then(()=>renderPluginInfo());
}

// ====================================================================
//  Barre de menus (chrome desktop) : dropdowns + panneau repliable.
//  Ne fait QUE relocaliser/ouvrir des contrôles existants (mêmes ids) ;
//  la logique métier reste dans bindUI()/bindStage2Features().
// ====================================================================
let _openMenu=null;   // élément .mb-menu actuellement ouvert (un seul à la fois)
function closeMenu(){
  if(!_openMenu) return;
  _closeSubmenu();    // referme aussi un éventuel flyout interne
  _openMenu.classList.remove('open');
  const top=_openMenu.querySelector('.mb-top'); if(top) top.setAttribute('aria-expanded','false');
  _openMenu=null;
}

// --- sous-menus (flyout) repliables dans un dropdown : ex. « Correction auto » ---
function _closeSubmenu(){
  document.querySelectorAll('#menubar .mb-sub.open').forEach(sub=>{
    sub.classList.remove('open');
    const top=sub.querySelector('.mb-sub-top'); if(top) top.setAttribute('aria-expanded','false');
  });
}
function _bindSubmenu(){
  const sub=$('correct-sub'); if(!sub) return;
  const btn=$('correct-sub-btn'); if(!btn) return;
  btn.addEventListener('click', e=>{
    e.stopPropagation();   // ne ferme PAS le dropdown Outils parent
    const open=sub.classList.toggle('open');
    btn.setAttribute('aria-expanded', open?'true':'false');
  });
  // clics dans le flyout (radios, bouton, statut) : ne ferment pas le menu.
  const panel=$('correct-sub-panel');
  if(panel) panel.addEventListener('click', e=>e.stopPropagation());
}
function openMenu(menu){
  if(_openMenu===menu) return;
  closeMenu();
  menu.classList.add('open');
  const top=menu.querySelector('.mb-top'); if(top) top.setAttribute('aria-expanded','true');
  _openMenu=menu;
}
// --- panneau latéral repliable (état persisté dans localStorage) ---
const SIDE_COLLAPSE_KEY='pe.sideCollapsed';
function setSideCollapsed(collapsed){
  const app=$('app'); if(!app) return;
  app.classList.toggle('side-collapsed', collapsed);
  localStorage.setItem(SIDE_COLLAPSE_KEY, collapsed?'1':'0');
  // miroir dans le menu Affichage (« Panneau latéral » coché = visible)
  const it=$('t-panel');
  if(it){ it.classList.toggle('on', !collapsed); it.setAttribute('aria-checked', collapsed?'false':'true'); }
  if(typeof resize==='function') setTimeout(resize, 240);   // recadre le canvas après la transition
}
function toggleSideCollapsed(){ setSideCollapsed(!$('app').classList.contains('side-collapsed')); }

function bindMenubar(){
  const bar=$('menubar'); if(!bar) return;
  const menus=Array.from(bar.querySelectorAll('.mb-menu'));

  // clic sur un libellé de menu : ouvre/ferme son dropdown (un seul ouvert).
  menus.forEach(menu=>{
    const top=menu.querySelector('.mb-top'); if(!top) return;
    const drop=menu.querySelector('.mb-drop');
    top.addEventListener('click', e=>{
      e.stopPropagation();
      // « Paramètres » : pas de dropdown, ouvre directement le dialogue.
      if(!drop){ closeMenu(); toggleSettings(); return; }
      (menu.classList.contains('open')) ? closeMenu() : openMenu(menu);
    });
    // survol d'un autre libellé alors qu'un menu est ouvert -> bascule (UX desktop)
    top.addEventListener('mouseenter', ()=>{ if(_openMenu && _openMenu!==menu && drop) openMenu(menu); });
    // sélectionner un item ferme le menu — SAUF les items internes d'un sous-menu
    // (flyout) : ceux-là gèrent leur propre fermeture (cf. _bindSubmenu).
    if(drop) drop.querySelectorAll('.mb-item').forEach(it=>{
      if(it.closest('.mb-sub')) return;        // item dans un flyout : pas de fermeture auto
      it.addEventListener('click', ()=>closeMenu());
    });
  });

  // --- sous-menu repliable « Correction automatique » (flyout dans Outils) ---
  _bindSubmenu();

  // clic en dehors de la barre -> ferme le menu ouvert
  document.addEventListener('pointerdown', e=>{ if(_openMenu && !bar.contains(e.target)) closeMenu(); });
  // navigation clavier : Échap ferme ; flèches gauche/droite changent de menu ouvert
  document.addEventListener('keydown', e=>{
    if(e.key==='Escape' && _openMenu){ const t=_openMenu.querySelector('.mb-top'); closeMenu(); if(t) t.focus(); return; }
    if(!_openMenu) return;
    if(e.key==='ArrowRight'||e.key==='ArrowLeft'){
      e.preventDefault();
      const withDrop=menus.filter(m=>m.querySelector('.mb-drop'));
      const i=withDrop.indexOf(_openMenu); if(i<0) return;
      const ni=(i + (e.key==='ArrowRight'?1:withDrop.length-1)) % withDrop.length;
      openMenu(withDrop[ni]); const t=withDrop[ni].querySelector('.mb-top'); if(t) t.focus();
    }
  });

  // --- item « Métriques » (menu Affichage) : montre/cache #metrics-panel ---
  const mItem=$('t-metrics');
  if(mItem) mItem.addEventListener('click', ()=>{
    const on=!metricsPanelOn;
    showMetricsPanel(on);
    if(on && typeof renderMetricsPanel==='function') renderMetricsPanel();
    mItem.classList.toggle('on', on);
    mItem.setAttribute('aria-checked', on?'true':'false');
  });

  // --- item « Panneau latéral » (menu Affichage) + boutons repli/expand ---
  const pItem=$('t-panel');
  if(pItem) pItem.addEventListener('click', toggleSideCollapsed);
  const sc=$('side-collapse'); if(sc) sc.onclick=()=>setSideCollapsed(true);
  const se=$('side-expand');   if(se) se.onclick=()=>setSideCollapsed(false);
  // restaure l'état persisté du panneau
  setSideCollapsed(localStorage.getItem(SIDE_COLLAPSE_KEY)==='1');

  // --- menu Aide : « Raccourcis clavier » + « Version / À propos » ---
  // On (re)branche ici, APRÈS le binding générique des .mb-item (qui ferme le
  // menu) : la fermeture du dropdown et l'ouverture de la modale coexistent.
  const hb=$('help-btn');
  if(hb) hb.addEventListener('click', ()=>{ closeMenu(); openShortcuts(); });
  const ab=$('about-btn');
  if(ab) ab.addEventListener('click', ()=>{ closeMenu(); openAbout(); });
}

// « Version / À propos » : petite boîte avec la version du serveur. On rafraîchit
// GET /info au passage si on ne l'a pas encore (affichage robuste même offline).
function openAbout(){
  const dlg=$('about-dialog'); if(!dlg) return;
  const fill=()=>{
    const body=$('about-body'); if(!body) return;
    const ver=(_serverInfo&&_serverInfo.version)
      ? ('<code>v'+escHtml(String(_serverInfo.version))+'</code>')
      : escHtml(t('menu.about.nover'));
    body.innerHTML=escHtml(t('menu.about.body'))+'<br>'+escHtml(t('about.version'))+' '+ver;
  };
  fill();
  if(!_serverInfo){ fetchServerInfo().then(()=>{ renderPluginInfo(); fill(); }); }
  if(_modalStack.includes(dlg)) return;
  openModal(dlg, document.activeElement, $('about-close'));
}
function closeAbout(){ const dlg=$('about-dialog'); if(dlg) closeModal(dlg); }

// Active/desactive les controles gates selon la presence d'un clip (DATA).
// N'altere PAS les controles deja geres par leur propre logique (mode sol :
// floor-tx/ty/h/reset/save ; remplis par doRefit/floor ; pastille Save).
function gateControls(){
  const enabled = !!DATA;
  GATED_CTRL_IDS.forEach(id=>{ const e=$(id); if(e) e.disabled=!enabled; });
  if(typeof renderSavePill==='function') renderSavePill();
}

function buildFromData(){
  N=DATA.N; T=DATA.T; J=DATA.J;
  joints = Float32Array.from(DATA.joints);
  edited = Float32Array.from(joints);
  stretchPts = Array.from({length:N},()=>[]);   // une liste de points cibles vide par danseur
  stepCum = Array.from({length:N},()=>({x:0,y:0,z:0}));   // offset constant cumule par danseur

  const c = centroid();
  camera.position.set(c.x, c.y-4.5, c.z+0.5);
  orbit.target.set(c.x, c.y, c.z); orbit.update();

  const sphereGeo = new THREE.SphereGeometry(0.03, 10, 8);
  for(let n=0;n<N;n++){
    const col = DCOL[n%DCOL.length];
    const mat = new THREE.MeshBasicMaterial({color:col});
    const spheres=[];
    for(let j=0;j<J;j++){
      const m = new THREE.Mesh(sphereGeo, mat.clone());
      m.userData = {n, j};
      scene.add(m); spheres.push(m);
    }
    const edges=[];
    for(let j=1;j<J;j++){ const p=DATA.parents[j]; if(p>=0){ edges.push(j,p); } }
    const bgeo = new THREE.BufferGeometry();
    const posAttr = new THREE.BufferAttribute(new Float32Array(J*3),3);
    bgeo.setAttribute('position', posAttr);
    bgeo.setIndex(edges);
    const bmat = new THREE.LineBasicMaterial({color:col});
    const bones = new THREE.LineSegments(bgeo, bmat);
    scene.add(bones);
    dancers.push({spheres, bones, posAttr});
  }

  // maillage : plus de chargement "toutes frames" ici. Le toggle « Maillage »
  // charge les faces une fois puis les verts de la frame courante a la demande
  // (voir toggleMesh / fetchMeshFrame). Le refit cree ses propres meshObjs.
  buildBillboard();
  buildFloor();
  buildShadowFloor();

  const sd=$('sel-d'); for(let n=0;n<N;n++){ const o=document.createElement('option'); o.value=n;o.textContent=t('dancer.label')+' '+n; sd.appendChild(o);}
  const sj=$('sel-j'); for(let j=0;j<J;j++){ const o=document.createElement('option'); o.value=j;o.textContent=j+' '+SMPL_NAMES[j]; sj.appendChild(o);}
  updateSwatch();

  setFrame(0); updateJointFields();
  $('frame').max=T-1; $('total').textContent='/'+(T-1);
  setMusicSrc();
}

function updateSwatch(){
  const sw=$('dancer-swatch'); if(sw) sw.style.background='#'+DCOL[selDancer%DCOL.length].toString(16).padStart(6,'0');
}

// ====================================================================
//  Maillage SMPL "frame courante" — genere a la demande par le backend.
//  /mesh_faces (1x) -> N THREE.Mesh ; /mesh_frame?frame=T -> verts de la frame.
//  Cache LRU des frames deja recuperees + debounce du scrub rapide.
// ====================================================================
const MESH_V = 6890;

// construit N meshes (faces partagees) avec une couleur par danseur.
function buildLiveMeshObjs(faces){
  meshFaces = faces;
  const faceArr = Array.from(faces);
  for(let n=0;n<N;n++){
    const g = new THREE.BufferGeometry();
    g.setAttribute('position', new THREE.BufferAttribute(new Float32Array(MESH_V*3),3));
    g.setIndex(faceArr);
    g.computeVertexNormals();
    const mat = new THREE.MeshStandardMaterial({color:DCOL[n%DCOL.length],
      transparent:true, opacity:0.82, roughness:0.55, metalness:0.0, side:THREE.DoubleSide});
    const mesh = new THREE.Mesh(g, mat); mesh.visible=true;
    mesh.castShadow=true; mesh.receiveShadow=true;
    mesh.frustumCulled=false;   // verts mis a jour a la volee -> bounding sphere obsolete : on desactive le culling (sinon le maillage disparait selon l'angle de vue)
    scene.add(mesh); meshObjs.push(mesh);
  }
}

// applique les verts (Float32Array N*V*3) de la frame aux geometries.
// Les danseurs en TRANSLATION PURE sont IGNORES ici : leur maillage est pilote
// a part par applyRigidLiveFrame (verts de base + offset, jamais refites), sinon
// un fetch /mesh_frame (verts non offsetes) ou une frame cache ecraserait leur
// position. `skipRigid` (defaut true) garde cette regle ; false force tout.
function applyMeshVerts(verts, skipRigid){
  if(skipRigid===undefined) skipRigid=true;
  const rigid = skipRigid ? (()=>{ const s=new Set(); for(let n=0;n<N;n++){ const d=dancerRigidOffset(n); if(d.rigid&&d.edits) s.add(n); } return s; })() : null;
  for(let n=0;n<N && n<meshObjs.length;n++){
    if(rigid && rigid.has(n)) continue;   // pilote par applyRigidLiveFrame
    const pos=meshObjs[n].geometry.attributes.position.array;
    pos.set(verts.subarray(n*MESH_V*3, (n+1)*MESH_V*3));
    meshObjs[n].geometry.attributes.position.needsUpdate=true;
    meshObjs[n].geometry.computeVertexNormals();
  }
  refreshFloorDist();      // verts affiches mis a jour -> recale les traits
}

// range une frame dans le cache LRU (eviction de la plus ancienne).
function cacheMeshFrame(t, verts){
  if(meshCache.has(t)) meshCache.delete(t);  // refresh ordre LRU
  meshCache.set(t, verts);
  while(meshCache.size>MESH_CACHE_MAX){
    const oldest=meshCache.keys().next().value;
    meshCache.delete(oldest);
  }
}

// Decode le corps d'une reponse /mesh_frame. Le backend envoie maintenant les
// verts en float16 (moitie des octets, en-tete X-Mesh-Dtype: f16) -> on
// reconvertit en Float32Array via THREE.DataUtils.fromHalfFloat (three r160).
function decodeVerts(buf){
  const h=new Uint16Array(buf);
  const f=new Float32Array(h.length);
  for(let i=0;i<h.length;i++) f[i]=THREE.DataUtils.fromHalfFloat(h[i]);
  return f;
}

// recupere les verts de la frame t depuis le backend et les range au cache (sans affichage).
// renvoie le Float32Array, ou null en cas d'echec. Anti-doublon via meshInflight.
async function loadMeshVerts(t){
  if(meshCache.has(t)) return meshCache.get(t);
  if(meshInflight.has(t)) return null;          // deja en vol : on n'empile pas
  meshInflight.add(t);
  try{
    const r=await fetch(`/mesh_frame?clip=${encodeURIComponent(CLIP_NAME)}&source=${CLIP_SOURCE}&frame=${t}&v=${MESH_VERSION}`);
    if(!r.ok) throw new Error(`/mesh_frame ${r.status}`);
    const v=decodeVerts(await r.arrayBuffer());
    cacheMeshFrame(t,v);
    return v;
  }catch(e){
    setMeshStatus('✗ '+e.message, '#ff7777');
    return null;
  }finally{
    meshInflight.delete(t);
  }
}

// recupere (cache ou reseau) les verts de la frame t et les affiche, si encore pertinent.
async function fetchMeshFrame(t){
  if(!meshLive) return;
  if(meshCache.has(t)){
    const v=meshCache.get(t); cacheMeshFrame(t,v);   // bump LRU
    if(curFrame===t && meshVisible()) applyMeshVerts(v);
    return;
  }
  const seq=++meshFetchSeq;
  const v=await loadMeshVerts(t);
  // n'affiche que si on est toujours sur cette frame et le maillage visible
  if(v && seq===meshFetchSeq && curFrame===t && meshVisible()) applyMeshVerts(v);
}

// ---- prechargement en fenetre glissante (lecture) ----
// remplit le cache avec ~MESH_PREFETCH_AHEAD frames devant curFrame, sans depasser
// MESH_PREFETCH_CONC fetchs concurrents. Re-arme tant que la lecture continue.
function pumpMeshPrefetch(){
  if(!meshPrefetchOn || !meshLive || !meshVisible()) return;
  let started=0;
  for(let k=1; k<=MESH_PREFETCH_AHEAD && meshInflight.size<MESH_PREFETCH_CONC; k++){
    const t=(curFrame+k)%T;
    if(meshCache.has(t) || meshInflight.has(t)) continue;
    // loadMeshVerts ne bloque pas la boucle ; on relance la pompe a chaque arrivee
    loadMeshVerts(t).then(()=>{ pumpMeshPrefetch(); });
    started++;
  }
  return started;
}

// (re)demarre / arrete le prechargement selon l'etat de lecture + visibilite maillage.
function syncMeshPrefetch(){
  const want = playing && meshLive && meshVisible();
  if(want && !meshPrefetchOn){ meshPrefetchOn=true; pumpMeshPrefetch(); }
  else if(!want){ meshPrefetchOn=false; }
  // HUD maillage : actif tant qu'il reste des fetchs en vol pendant la lecture.
  setLoadHud('mesh', want && meshInflight.size>0);
  syncBgPrefetch();
}

// ---- indicateur discret « mise en cache du clip… NN % » (non bloquant) ----
function setBufferStatus(pct){
  const el=$('buffer-status'); if(!el) return;
  if(pct==null || pct>=100){ el.hidden=true; el.textContent=''; return; }
  el.hidden=false;
  el.textContent=tf('buffer.caching',{pct:Math.max(0,Math.min(99,Math.floor(pct)))});
}

// ---- mise en cache de TOUT le clip en tache de fond ----
// But : peupler le cache HTTP du navigateur (octets f16 immutables) pour TOUTES
// les frames 0..T-1, afin que lecture/scrub deviennent instantanes (cache hits)
// une fois le clip bufferise. On ne garde pas tous les resultats en memoire (le
// navigateur garde les octets) : on decode/range au plus MESH_CACHE_MAX frames
// via loadMeshVerts (cache LRU borne) ; le reste n'est qu'un fetch « warm cache ».
// Concurrence douce (MESH_BUFFER_CONC), en pause pendant la lecture ou tant que
// le prechargement de fenetre travaille, pour ne jamais concurrencer le playhead.
// Annulable : guard par meshBufferToken (incremente a chaque chargement de clip).
async function bufferWholeClip(){
  if(!CLIP_NAME || !meshLive || !T) { setBufferStatus(null); return; }
  const token=++meshBufferToken;        // ce remplissage est lie a ce token
  const total=T;
  let next=0;                           // prochaine frame a planifier
  let done=0;                           // frames traitees (en cache ou fetchees)
  _bufPct=0; _bufDone=false;

  // pause UNIQUEMENT pendant la lecture (pour ne pas voler la bande passante au
  // playhead) ; sinon les workers tournent en parallele (sature le lien). NE PAS
  // attendre meshInflight, sinon les workers se bloquent l'un l'autre (=> 1 seul
  // a la fois). Sort si le clip a change (token perime).
  const idle=()=>new Promise(res=>{
    const tick=()=>{
      if(token!==meshBufferToken) return res(false);
      if(!playing && meshLive) return res(true);
      setTimeout(tick, 200);
    };
    tick();
  });

  // un « worker » : prend des frames une a une jusqu'a epuisement / annulation.
  async function worker(){
    while(token===meshBufferToken){
      // si on a deja tout, on s'arrete.
      if(next>=total) return;
      if(!(await idle())) return;       // clip change -> annule
      const t0=next++;
      if(meshCache.has(t0)){ done++; continue; }
      // fetch « warm cache » : URL versionnee identique a loadMeshVerts ->
      // sert au cache HTTP. On evite de gonfler la memoire : on ne range au
      // cache LRU que si on a de la place, sinon on jette juste les octets.
      try{
        if(meshCache.size<MESH_CACHE_MAX){
          await loadMeshVerts(t0);      // decode + range (LRU borne)
        }else{
          const url=`/mesh_frame?clip=${encodeURIComponent(CLIP_NAME)}`+
            `&source=${CLIP_SOURCE}&frame=${t0}&v=${MESH_VERSION}`;
          await fetch(url);             // peuple seulement le cache HTTP
        }
      }catch(_){ /* reseau : on reessaiera pas, on continue */ }
      if(token!==meshBufferToken) return;
      done++;
      _bufPct=100*done/total;
      setBufferStatus(_bufPct);
    }
  }

  setBufferStatus(0);
  const workers=[];
  for(let i=0;i<MESH_BUFFER_CONC;i++) workers.push(worker());
  await Promise.all(workers);
  if(token===meshBufferToken){ _bufDone=true; setBufferStatus(null); }   // 100 %
}

// ---- vrai si le mode remove-bg/crop du fond est actif (prefetch pertinent). ----
function bgRemoveActive(){
  const cb=$('bg-remove');
  return !!(bg && DATA && DATA.frames && DATA.frames.length && cb && cb.checked);
}

// ---- prechargement du FOND (crop serveur /bg_nobg) en fenetre glissante. ----
// Meme principe que pumpMeshPrefetch : remplit bgSegCache devant curFrame, borne
// a BG_PREFETCH_CONC fetchs concurrents (_serverNoBgPending). Ne tourne que si le
// remove-bg est actif. Le fallback navigateur n'est PAS precharge (couteux CPU).
function pumpBgPrefetch(){
  if(!bgPrefetchOn || !bgRemoveActive() || _serverNoBgFailed) return;
  for(let k=1; k<=BG_PREFETCH_AHEAD && _serverNoBgPending.size<BG_PREFETCH_CONC; k++){
    const tt=(curFrame+k)%T;
    if(bgSegCache[tt] || _serverNoBgPending.has(tt)) continue;
    _loadServerNoBg(tt);   // re-arme via setLoadHud quand le fetch retombe (cf. _loadServerNoBg)
  }
  setLoadHud('bg', _serverNoBgPending.size>0);
}

// (re)demarre / arrete le prechargement du fond selon lecture + remove-bg actif.
function syncBgPrefetch(){
  const want = playing && bgRemoveActive() && !_serverNoBgFailed;
  if(want && !bgPrefetchOn){ bgPrefetchOn=true; pumpBgPrefetch(); }
  else if(!want){ bgPrefetchOn=false; if(!_serverNoBgPending.size) setLoadHud('bg', false); }
}

// ---- warm-up serveur du fond (one-shot, tout le clip) : POST /prewarm_bg. ----
// Demande au serveur de segmenter toutes les frames dans son cache disque ; les
// fetchs /bg_nobg suivants tombent alors dans le cache (plus de gel par frame).
// Degrade proprement si l'endpoint n'existe pas (vieux backend) : on retombe sur
// le comportement paresseux historique.
async function prewarmBg(){
  if(!bgRemoveActive()) return;
  const clip=CLIP_NAME || (DATA && DATA.name) || '';
  const source=CLIP_SOURCE || 'original';
  if(!clip) return;
  try{
    const r=await fetch('/prewarm_bg',{method:'POST',
      headers:{'Content-Type':'application/json'}, body:JSON.stringify({clip, source})});
    if(!r.ok) return;          // 404 ou autre : on n'insiste pas (fallback paresseux)
    pollPrewarmStatus(clip, source);
  }catch(_){ /* endpoint absent : fallback paresseux silencieux */ }
}

// polling GET /prewarm_status : spinner « Fond » + statut tant que le serveur
// prepare le fond. 404 -> on arrete proprement.
function pollPrewarmStatus(clip, source){
  if(_prewarmPollTimer) clearTimeout(_prewarmPollTimer);
  const tick=async()=>{
    // si on a change de clip entre-temps, on arrete.
    if((CLIP_NAME||'')!==clip){ setLoadHud('bg', _serverNoBgPending.size>0); return; }
    let j=null;
    try{
      const r=await fetch(`/prewarm_status?clip=${encodeURIComponent(clip)}&source=${encodeURIComponent(source)}`);
      if(r.ok) j=await r.json();
    }catch(_){}
    if(!j){ setLoadHud('bg', _serverNoBgPending.size>0); return; }   // 404 -> stop
    if(j.running){
      setLoadHud('bg', true);
      _segSetStatus('préparation du fond '+(j.done||0)+'/'+(j.total||0)+'…');
      _prewarmPollTimer=setTimeout(tick,1200);
    }else{
      _segSetStatus('fond prêt ✓');
      setLoadHud('bg', _serverNoBgPending.size>0);
    }
  };
  tick();
}

function meshVisible(){ return meshObjs.length>0 && meshObjs[0].visible; }
function setMeshStatus(msg,col){ const st=$('refit-status'); if(st){ st.style.color=col||''; st.textContent=msg; } }

// 1er clic « Maillage » ON : charge faces + verts frame courante (live).
async function enableLiveMesh(){
  if(!CLIP_NAME){
    setMeshStatus(t('mesh.noBackend'), '#ff7777');
    return false;
  }
  setMeshStatus(t('mesh.gen'), '#e7c14b');
  try{
    const r=await fetch(`/mesh_faces?clip=${encodeURIComponent(CLIP_NAME)}&source=${CLIP_SOURCE}`);
    if(!r.ok) throw new Error(`/mesh_faces ${r.status}`);
    const faces=new Int32Array(await r.arrayBuffer());
    buildLiveMeshObjs(faces);
    meshLive=true;
    await fetchMeshFrame(curFrame);
    setMeshStatus(t('mesh.ready'), '#7fd18b');
    syncMeshPrefetch();   // si on active le maillage pendant la lecture
    showMetricsPanel(true);   // mode live -> on montre aussi le panneau metriques
    return true;
  }catch(e){
    setMeshStatus('✗ '+e.message, '#ff7777');
    return false;
  }
}

// bascule du toggle « Maillage ».
async function toggleMesh(){
  // cas refit : des meshObjs existent deja (verts refites) -> simple visibilite
  if(meshObjs.length && !meshLive){
    const v=!meshObjs[0].visible; meshObjs.forEach(m=>m.visible=v);
    $('t-mesh').classList.toggle('on',v);
    showMetricsPanel(v);
    syncFloorDistAvail(); if(floorDistOn) refreshFloorDist();
    return;
  }
  if(!meshObjs.length){
    $('t-mesh').classList.add('on');
    const ok=await enableLiveMesh();
    if(!ok) $('t-mesh').classList.remove('on');
    syncFloorDistAvail();
    return;
  }
  // maillage live deja construit : bascule visibilite
  const v=!meshObjs[0].visible; meshObjs.forEach(m=>m.visible=v);
  $('t-mesh').classList.toggle('on',v);
  showMetricsPanel(v);
  if(v) requestMeshFrame(curFrame, true);
  syncMeshPrefetch();   // maillage masque pendant la lecture -> stoppe le prechargement
  syncFloorDistAvail(); if(floorDistOn) refreshFloorDist();
}

// demande l'affichage du maillage a la frame t (debounce le scrub rapide).
function requestMeshFrame(t, immediate){
  if(!meshLive || !meshVisible()) return;
  if(meshCache.has(t)){ fetchMeshFrame(t); return; }   // deja en cache : instantane
  if(meshDebounce) clearTimeout(meshDebounce);
  if(immediate){ fetchMeshFrame(t); return; }
  meshDebounce=setTimeout(()=>{ meshDebounce=null; if(curFrame===t) fetchMeshFrame(t); }, 90);
}

// ---- sol estime + correction manuelle ----
// Les variantes (raw/corrected/manual) viennent de floors.json via /load
// (DATA.floors). Le damier affiche la variante choisie ; le mode correction
// attache un gizmo au damier et recalcule le plan [a,b,c] depuis sa pose.
const FLOOR_SIZE=16, FLOOR_SQ=0.5;        // plan 16 m, cases de 0.5 m

// plan [a,b,c] d'une variante, ou null si absente.
function floorVariantPlane(name){
  const fl = DATA && DATA.floors;
  if(fl && fl[name]) return fl[name];
  // repli : ancien format (DATA.floor seul) -> corrected==raw==floor
  if((name==='corrected'||name==='raw') && DATA && DATA.floor) return DATA.floor;
  return null;
}

// construit / reconstruit le damier pour le plan [a,b,c] courant (floorPlane).
function buildFloor(){
  removeFloor();
  const fInfo = $('floor-info');
  // choisit la variante par defaut : manuel si present, sinon corrige.
  const fl = DATA && DATA.floors;
  if(fl){
    floorVariant = (fl.manual!=null) ? 'manual' : 'corrected';
  } else {
    floorVariant = 'corrected';
  }
  floorPlane = floorVariantPlane(floorVariant) || (DATA && DATA.floor) || null;
  syncFloorVariantUI();
  if(!floorPlane){
    setFloorOnDisabled(true);
    if(fInfo) fInfo.textContent=t('floor.none');
    if($('floor-edit')) $('floor-edit').disabled=true;
    return;
  }
  setFloorOnDisabled(false);
  if($('floor-edit')) $('floor-edit').disabled=false;
  makeFloorMesh();
  updateFloorInfo();
  updateFloorFields();
  syncFloorDistAvail();
}

// (re)cree le THREE.Mesh damier a partir de floorPlane (sans toucher aux infos UI).
function makeFloorMesh(){
  if(floorGrid){ removeFloor(); }
  const [a,b,c]=floorPlane;
  const ctr=centroid();
  const cx=ctr.x, cy=ctr.y, cz=a*ctr.x+b*ctr.y+c;
  const cv=document.createElement('canvas'); cv.width=cv.height=64;
  const cc=cv.getContext('2d');
  cc.fillStyle='#111'; cc.fillRect(0,0,64,64);
  cc.fillStyle='#f2f2f2'; cc.fillRect(0,0,32,32); cc.fillRect(32,32,32,32);
  const tex=new THREE.CanvasTexture(cv);
  tex.wrapS=tex.wrapT=THREE.RepeatWrapping;
  tex.repeat.set(FLOOR_SIZE/(2*FLOOR_SQ), FLOOR_SIZE/(2*FLOOR_SQ));
  tex.magFilter=THREE.NearestFilter; tex.minFilter=THREE.NearestFilter;
  const geo=new THREE.PlaneGeometry(FLOOR_SIZE,FLOOR_SIZE);
  const mat=new THREE.MeshBasicMaterial({map:tex, side:THREE.DoubleSide,
    transparent:true, opacity:0.78, depthWrite:false});
  const g=new THREE.Mesh(geo, mat);
  const normal=new THREE.Vector3(-a,-b,1).normalize();
  g.quaternion.setFromUnitVectors(new THREE.Vector3(0,0,1), normal);
  g.position.set(cx,cy,cz);
  g.renderOrder=-1;                       // dessine sous les danseurs/vidéo
  g.userData.isFloor=true;                // exclu du picking de joints
  g.visible=floorOnChecked();
  scene.add(g); floorGrid=g;
}

// recalcule le plan [a,b,c] depuis l'orientation + position du mesh damier.
// normale = quaternion·(0,0,1) ; a=-nx/nz, b=-ny/nz ; c tel que le plan passe
// par la position du mesh.
function planeFromFloorMesh(){
  const n=new THREE.Vector3(0,0,1).applyQuaternion(floorGrid.quaternion);
  if(Math.abs(n.z)<1e-6) return floorPlane;   // garde-fou (plan vertical degenere)
  const a=-n.x/n.z, b=-n.y/n.z;
  const p=floorGrid.position;
  const c=p.z - a*p.x - b*p.y;
  return [a,b,c];
}

// repositionne le damier pour le plan [a,b,c] (sans le recreer) — utilise par
// l'edition via les champs numeriques.
function applyPlaneToFloorMesh(plane){
  if(!floorGrid) return;
  const [a,b,c]=plane;
  const ctr=centroid();
  const cx=ctr.x, cy=ctr.y, cz=a*ctr.x+b*ctr.y+c;
  const normal=new THREE.Vector3(-a,-b,1).normalize();
  floorGrid.quaternion.setFromUnitVectors(new THREE.Vector3(0,0,1), normal);
  floorGrid.position.set(cx,cy,cz);
}

function floorTiltDeg(plane){
  const [a,b]=plane; return Math.atan(Math.hypot(a,b))*180/Math.PI;
}

// libelle sous le toggle Sol : variante + inclinaison.
function updateFloorInfo(){
  const fInfo=$('floor-info'); if(!fInfo) return;
  if(!floorPlane){ fInfo.textContent=t('floor.none'); return; }
  const tilt=floorTiltDeg(floorPlane);
  const meta=DATA.floor_meta||{};
  let s=`${t('floor.tilt')} ${tilt.toFixed(1)}°`;
  if(meta.cam_tilt_deg!=null) s+=` · cam ${meta.cam_tilt_deg.toFixed(1)}°`;
  fInfo.textContent=s;
}

// (de)grise les options du selecteur de variante selon ce qui existe + selectionne.
function syncFloorVariantUI(){
  const sel=$('floor-variant'); if(!sel) return;
  ['raw','corrected','manual'].forEach(name=>{
    const opt=sel.querySelector(`option[value="${name}"]`);
    if(opt) opt.disabled = (floorVariantPlane(name)==null);
  });
  sel.value=floorVariant;
}

// champs Inclinaison X/Y (deg) + Hauteur (m) depuis floorPlane.
// inclinaison X = pente dz/dx = a -> atan(a) ; inclinaison Y = atan(b).
// hauteur = z du plan au centroide des danseurs.
function updateFloorFields(){
  if(!floorPlane) return;
  const [a,b,c]=floorPlane;
  const ctr=centroid();
  $('floor-tx').value=(Math.atan(a)*180/Math.PI).toFixed(2);
  $('floor-ty').value=(Math.atan(b)*180/Math.PI).toFixed(2);
  $('floor-h').value =(a*ctr.x+b*ctr.y+c).toFixed(3);
}

function removeFloor(){
  if(floorGrid){ if(tcontrols.object===floorGrid) tcontrols.detach();
    scene.remove(floorGrid);
    floorGrid.traverse(o=>{ o.geometry?.dispose?.(); if(o.material){ (Array.isArray(o.material)?o.material:[o.material]).forEach(m=>m.dispose?.()); } });
    floorGrid=null; }
}

// ---- capteur d'ombre au sol (plan horizontal, ne montre QUE les ombres) ----
// monde z-up : PlaneGeometry est dans le plan XY (normale +Z = horizontal),
// pas de rotation. Place a la hauteur des pieds (z min des joints au chargement,
// sinon 0). Exclu du picking (isFloor) et retire au teardown.
function buildShadowFloor(){
  if(shadowFloor) removeShadowFloor();
  let zMin=Infinity;
  for(let i=2;i<joints.length;i+=3){ if(joints[i]<zMin) zMin=joints[i]; }
  if(!isFinite(zMin)) zMin=0;
  const c=centroid();
  const geo=new THREE.PlaneGeometry(40,40);
  const mat=new THREE.ShadowMaterial({opacity:0.35});
  const g=new THREE.Mesh(geo, mat);
  g.position.set(c.x, c.y, zMin);
  g.receiveShadow=true;
  g.renderOrder=-2;
  g.userData.isFloor=true;          // exclu du picking de joints
  scene.add(g); shadowFloor=g;
}
// ====================================================================
//  Distance au sol — pour chaque danseur, chaque pied (gauche/droit), trace
//  un trait du vertex le PLUS BAS du pied (distance signee au plan minimale)
//  jusqu'a sa projection sur le sol, le long de la normale n=(-a,-b,1).
//  Bleu = vertex au-dessus du sol (flotte) ; rouge = en-dessous (penetre).
//  S'appuie sur les verts AFFICHES (meshObjs[n].geometry.attributes.position)
//  -> requiert le maillage actif ; sinon le toggle est grise.
// ====================================================================
let floorDistOn=false;           // etat du toggle
let floorDistLines=[];           // THREE.Line (2 par danseur : gauche/droit)
let footMasks=null;              // {left:[...], right:[...]} (cache, fetch 1x)
let footMasksPromise=null;

const FD_BLUE=0x0033ff, FD_RED=0xff0000;   // bleu/rouge vifs saturés (bien visibles)

// recupere les indices de vertices de pied (semelles G/D) une seule fois.
async function ensureFootMasks(){
  if(footMasks) return footMasks;
  if(footMasksPromise) return footMasksPromise;
  footMasksPromise=(async()=>{
    try{
      const r=await fetch('/foot_masks');
      if(!r.ok) throw new Error(`/foot_masks ${r.status}`);
      const j=await r.json();
      footMasks={left:j.left||[], right:j.right||[]};
    }catch(e){ footMasks=null; }
    finally{ footMasksPromise=null; }
    return footMasks;
  })();
  return footMasksPromise;
}

// (de)grise le toggle « Distance au sol » selon la dispo du maillage + sol.
function syncFloorDistAvail(){
  const btn=$('floor-dist'); if(!btn) return;
  const ok = meshVisible() && !!floorPlane;
  btn.disabled=!ok;
  if(!ok && floorDistOn){ floorDistOn=false; btn.classList.remove('on'); removeFloorDistLines(); }
  btn.classList.toggle('on', floorDistOn && ok);
}

function removeFloorDistLines(){
  for(const l of floorDistLines){ scene.remove(l);
    l.geometry?.dispose?.(); l.material?.dispose?.(); }
  floorDistLines=[];
}

// (re)construit les traits de distance au sol depuis les verts AFFICHES.
function rebuildFloorDistLines(){
  removeFloorDistLines();
  if(!floorDistOn || !floorPlane || !footMasks) return;
  if(!meshVisible() || !meshObjs.length) return;
  const [a,b,c]=floorPlane;
  // normale unitaire du plan z=a*x+b*y+c : n=(-a,-b,1) normalisee.
  const nx=-a, ny=-b, nz=1; const nlen=Math.hypot(nx,ny,nz);
  const ux=nx/nlen, uy=ny/nlen, uz=nz/nlen;
  // distance SIGNEE d'un point au plan = (z-(a*x+b*y+c)) / |n|   (>0 au-dessus)
  const denom=nlen;
  for(let n=0;n<N && n<meshObjs.length;n++){
    const pos=meshObjs[n].geometry.attributes.position.array;
    for(const side of ['left','right']){
      const idxs=footMasks[side]; if(!idxs||!idxs.length) continue;
      let bestSigned=Infinity, bx=0,by=0,bz=0;
      for(let k=0;k<idxs.length;k++){
        const vi=idxs[k]*3;
        const x=pos[vi], y=pos[vi+1], z=pos[vi+2];
        const sd=(z-(a*x+b*y+c))/denom;      // distance signee
        if(sd<bestSigned){ bestSigned=sd; bx=x;by=y;bz=z; }
      }
      if(!isFinite(bestSigned)) continue;
      // projection du vertex sur le plan le long de la normale : p - sd*u
      const px=bx-bestSigned*ux, py=by-bestSigned*uy, pz=bz-bestSigned*uz;
      const col=(bestSigned>0)?FD_BLUE:FD_RED;
      // trait = CYLINDRE fin (THREE.Line fait toujours 1px en WebGL -> invisible).
      const p0=new THREE.Vector3(bx,by,bz), p1=new THREE.Vector3(px,py,pz);
      const dir=new THREE.Vector3().subVectors(p1,p0); const len=dir.length();
      if(len<1e-5) continue;
      const g=new THREE.CylinderGeometry(0.017,0.017,len,10);
      const mat=new THREE.MeshBasicMaterial({color:col, depthTest:false});
      const line=new THREE.Mesh(g,mat);
      line.position.copy(p0).add(p1).multiplyScalar(0.5);
      line.quaternion.setFromUnitVectors(new THREE.Vector3(0,1,0), dir.normalize());
      line.renderOrder=10;
      line.userData.isFloor=true;          // exclu du picking de joints
      line.userData.floorDist=true;
      line.userData.signed=bestSigned;     // pour les tests/hooks
      line.frustumCulled=false;
      scene.add(line); floorDistLines.push(line);
    }
  }
}

// appele a chaque changement de frame/edition/sol quand le toggle est actif.
function refreshFloorDist(){
  if(!floorDistOn) return;
  if(!meshVisible() || !floorPlane){ removeFloorDistLines(); return; }
  rebuildFloorDistLines();
}

async function setFloorDist(on){
  const btn=$('floor-dist');
  if(on){
    if(!meshVisible() || !floorPlane){ syncFloorDistAvail(); return; }
    await ensureFootMasks();
    if(!footMasks){ floorDistOn=false; if(btn) btn.classList.remove('on'); return; }
    floorDistOn=true; if(btn) btn.classList.add('on');
    rebuildFloorDistLines();
  } else {
    floorDistOn=false; if(btn) btn.classList.remove('on');
    removeFloorDistLines();
  }
}

function removeShadowFloor(){
  if(shadowFloor){ scene.remove(shadowFloor);
    shadowFloor.geometry?.dispose?.(); shadowFloor.material?.dispose?.();
    shadowFloor=null; }
}

// ---- variante affichee ----
function selectFloorVariant(name){
  const plane=floorVariantPlane(name);
  if(!plane) return;
  floorVariant=name;
  floorPlane=plane.slice();
  if(floorGrid){ applyPlaneToFloorMesh(floorPlane); }
  else { makeFloorMesh(); }
  updateFloorInfo(); updateFloorFields(); syncFloorVariantUI();
  if(floorDistOn) refreshFloorDist();
}

// ---- mode correction du sol ----
function setFloorEditMode(on){
  if(on && !floorPlane) return;
  floorEditMode=!!on;
  $('floor-edit').classList.toggle('on',floorEditMode);
  $('floor-edit').textContent = floorEditMode ? t('floor.editon') : t('floor.editoff');
  ['floor-tx','floor-ty','floor-h','floor-reset','floor-save'].forEach(id=>{ const e=$(id); if(e) e.disabled=!floorEditMode; });
  if(floorEditMode){
    // s'affiche forcement quand on edite
    setFloorOnChecked(true); if(floorGrid) floorGrid.visible=true;
    // exclusivite : on coupe l'edition danseur/joint pendant la correction du sol
    dancerMoveMode=false; bgMoveMode=false; $('bg-move').classList.remove('on');
    tcontrols.detach();
    tcontrols.setMode('rotate');
    tcontrols.attach(floorGrid);
    updateFloorFields();
  } else {
    if(tcontrols.object===floorGrid) tcontrols.detach();
    // rend la main a l'edition danseur/joint selon l'accordeon
    dancerMoveMode = $('acc-global') && $('acc-global').open;
    attachGizmo();
  }
}

// appele a chaque manip du gizmo du damier : recalcule + reaffiche le plan.
function onFloorGizmo(){
  floorPlane=planeFromFloorMesh();
  // re-ancre proprement au centroide (garde l'inclinaison + la hauteur du plan)
  applyPlaneToFloorMesh(floorPlane);
  updateFloorFields(); updateFloorInfo();
  if(floorDistOn) refreshFloorDist();
}

// edition par champs numeriques : reconstruit le plan puis repositionne le damier.
function applyFloorFields(){
  if(!floorEditMode || !floorPlane) return;
  const txd=parseFloat($('floor-tx').value)||0;
  const tyd=parseFloat($('floor-ty').value)||0;
  const h  =parseFloat($('floor-h').value)||0;
  const a=Math.tan(txd*Math.PI/180);
  const b=Math.tan(tyd*Math.PI/180);
  const ctr=centroid();
  // hauteur = z au centroide -> c = h - a*cx - b*cy
  const c=h - a*ctr.x - b*ctr.y;
  floorPlane=[a,b,c];
  applyPlaneToFloorMesh(floorPlane);
  updateFloorInfo();
  if(floorDistOn) refreshFloorDist();
}

// enregistre floorPlane comme sol manuel (floor_manual) pour ce clip.
let floorSaveBusy=false;
async function saveFloor(){
  if(floorSaveBusy || !floorPlane) return;
  const st=$('floor-save-status');
  if(!CLIP_NAME){
    toast(t('gate.noclip'), 'err');
    return;
  }
  floorSaveBusy=true;
  st.style.color='#e7c14b'; st.textContent=t('floor.saving');
  try{
    const r=await fetch(`/save_floor?clip=${encodeURIComponent(CLIP_NAME)}`,{method:'POST',
      headers:{'Content-Type':'application/json'},
      body:JSON.stringify({plane:[floorPlane[0],floorPlane[1],floorPlane[2]]})});
    if(!r.ok) throw new Error(await errMsg(r));
    const j=await r.json();
    // la variante « manuel » devient dispo + selectionnee
    if(!DATA.floors) DATA.floors={};
    DATA.floors.manual=[j.plane[0],j.plane[1],j.plane[2]];
    DATA.floor=DATA.floors.manual;
    floorVariant='manual';
    syncFloorVariantUI();
    st.style.color='#7fd18b';
    st.textContent=`${t('floor.saved')} ${j.tilt_deg.toFixed(1)}°`;
    updateFloorInfo();
  }catch(e){
    st.style.color='#ff7777';
    st.textContent=t('floor.saveerr')+e.message;
  }finally{ floorSaveBusy=false; }
}

// relance l'estimation du sol (plugin de sol configuré) sur l'etat EDITE
// courant (joints deplaces/etires). POST /recompute_floor ->
// met DATA.floor au plan renvoye, reconstruit le damier (le sol s'ajuste aux
// nouvelles positions). Le resultat reste enregistrable via « Enregistrer le sol
// corrige » (saveFloor) ; ce recalcul ne fait que mettre a jour l'AFFICHAGE.
let floorRecomputeBusy=false;
async function recomputeFloor(){
  if(floorRecomputeBusy) return;
  const st=$('floor-recompute-status');
  if(!CLIP_NAME || !DATA){
    toast(t('gate.noclip'), 'err');
    return;
  }
  floorRecomputeBusy=true;
  const _btn=$('floor-recompute'); if(_btn) _btn.disabled=true;
  showOverlay(t('busy.floor'));
  if(st){ st.style.color='#e7c14b'; st.textContent=t('floor.recomputing'); }
  try{
    const body={ N, T, J, joints:Array.from(edited), iters:120 };
    const r=await fetch(
      `/recompute_floor?clip=${encodeURIComponent(CLIP_NAME)}&source=${CLIP_SOURCE}`,
      {method:'POST', headers:{'Content-Type':'application/json'},
       body:JSON.stringify(body)});
    if(!r.ok) throw new Error(await errMsg(r));
    const j=await r.json();
    const plane=[j.plane[0],j.plane[1],j.plane[2]];
    // met a jour le sol AFFICHE (DATA.floor) + reconstruit le damier sur le
    // nouveau plan, sans ecraser les variantes existantes (raw/corrected/...).
    if(DATA) DATA.floor=plane;
    floorPlane=plane.slice();
    setFloorOnDisabled(false);
    if($('floor-edit')) $('floor-edit').disabled=false;
    if(floorGrid){ applyPlaneToFloorMesh(floorPlane); }
    else { makeFloorMesh(); }
    updateFloorInfo(); updateFloorFields();
    if(floorDistOn) refreshFloorDist();
    if(st){
      st.style.color='#7fd18b';
      st.textContent=`${t('floor.recomputed')} ${j.tilt_deg.toFixed(1)}°`;
    }
  }catch(e){
    if(st){ st.style.color='#ff7777'; st.textContent=t('floor.recomputeerr')+e.message; }
  }finally{ floorRecomputeBusy=false; const b=$('floor-recompute'); if(b) b.disabled=false; hideOverlay(); }
}

// ===== Correcteur automatique (classe Corrector du pipeline) =====
// POST /correct_motion : le backend lance un SOUS-PROCESS python FRAIS qui
// reimporte corrector.py a neuf (donc version courante a chaque clic), applique
// la pipeline Corrector dans un pkl TEMPORAIRE (PAS de save), et renvoie les
// JOINTS corriges (N,T,24,3 z-up, meme convention que le clip charge) + les 7
// metriques EXACTES du clip corrige. Cote front, on applique ces joints comme
// une EDITION EN ATTENTE (comme une edition manuelle / un g-reset) : edited <-
// joints corriges, etat « modifie » (dirty), et on affiche les metriques exactes
// (ACTUEL = corrige vs DEPART = reference). AUCUNE sauvegarde : Melissa save
// elle-meme avec le bouton Save si elle veut.
let correctMotionBusy=false;
async function correctMotion(){
  if(correctMotionBusy) return;
  const st=$('correct-status');
  if(!CLIP_NAME || !DATA){
    toast(t('gate.noclip'), 'err');
    return;
  }
  // confirmation si des modifs sont en attente : la correction va les remplacer.
  // (elle reste reversible via une seule entree d'historique — voir snapshot ci-dessous.)
  if(saveDirty || undoStack.length){
    const ok=await confirmDialog(
      t('confirm.correct.title'), t('confirm.correct.body'),
      t('confirm.ok'), t('confirm.cancel'));
    if(!ok) return;
  }
  // instantane AVANT correction : permet d'annuler la correction en un seul Ctrl+Z.
  const _before=Float32Array.from(edited);
  correctMotionBusy=true;
  const btn=$('correct-motion'); if(btn) btn.disabled=true;
  showOverlay(t('busy.correct'));
  if(st){ st.style.color='#e7c14b'; st.textContent=t('correct.running'); }
  try{
    // ENTREE de la correction (toggle radio) :
    //  'raw'    -> le serveur corrige le pkl ORIGINAL BRUT (source=original
    //              forcee cote serveur) en ignorant les editions ; pas de body.
    //  'edited' -> on part de l'etat EDITE courant : on POST les joints edites
    //              (MEME format que /save_pkl : {N,T,J,joints,source}) ; le
    //              serveur les refit (lossy, comme une sauvegarde) puis corrige.
    const inSel=document.querySelector('input[name="correct-input"]:checked');
    const mode=(inSel && inSel.value==='edited') ? 'edited' : 'raw';
    let r;
    if(mode==='edited'){
      const body={ N, T, J, joints:Array.from(edited), source:CLIP_SOURCE, iters:150 };
      r=await fetch(
        `/correct_motion?clip=${encodeURIComponent(CLIP_NAME)}&mode=edited`,
        {method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)});
    }else{
      r=await fetch(
        `/correct_motion?clip=${encodeURIComponent(CLIP_NAME)}&mode=raw`,
        {method:'POST'});
    }
    const j=await r.json().catch(()=>({}));
    if(!r.ok || !j.ok) throw new Error(j.error || (j.log ? j.log.slice(-300) : `HTTP ${r.status}`));
    if(!Array.isArray(j.joints) || j.joints.length!==N*T*J*3)
      throw new Error(`joints corriges inattendus (recu ${j.joints?j.joints.length:0}, attendu ${N*T*J*3})`);

    // applique les joints corriges comme une EDITION (mime g-reset) : edited <-
    // joints renvoyes pour TOUTES les frames/danseurs ; on efface l'etirement
    // pour qu'un recompose ulterieur ne ecrase pas la correction.
    edited = Float32Array.from(j.joints);
    for(let n=0;n<N;n++){ stretchPts[n]=[]; }
    resetStepperVals();
    // une SEULE entree d'historique couvre toute la correction -> reversible en
    // un Ctrl+Z (restaure l'etat _before). On ne vide plus l'historique : on
    // empile un snapshot avant/apres (redo possible).
    redoStack.length=0;
    undoStack.push({type:'snapshot', before:_before, after:Float32Array.from(edited)});
    if(undoStack.length>UNDO_MAX) undoStack.shift();
    refreshUndoButtons();
    setFrame(curFrame);            // rafraichit les spheres (joints) de la frame courante
    markDirty();                   // etat « non sauvegarde » : Melissa save elle-meme

    // metriques EXACTES du clip corrige (du pkl temp) : ACTUEL = corrige, sans
    // refit lossy. metricsRef (DEPART) reste la reference du clip charge.
    if(j.metrics){
      metricsCur=j.metrics; metricsDirty=false;
      showMetricsPanel(true); renderMetricsPanel();
    }else{
      // pas de metriques renvoyees : on invalide pour inviter a « recalculer ».
      metricsCur=null; metricsDirty=true; renderMetricsPanel();
    }

    // si un maillage est affiche (mode live), on le recale sur les joints
    // corriges via /refit (l'init partant des poses corrigees, erreur ~0).
    // awaite : garde l'overlay « occupe » jusqu'a la fin du refit (pas de flash).
    if(meshShouldBeLive()){ await doRefit(); }

    // garde-fou : la correction ne doit PAS faire reapparaitre le fond video.
    // Si « Remove background » est coche, on re-applique le masque sur la frame
    // courante (setFrame/doRefit ont pu retomber sur la texture brute).
    reapplyBgRemove();

    if(st){ st.style.color='#7fd18b'; st.textContent=`${t('correct.done')} ${(j.time_s||0).toFixed(1)} s`; }
  }catch(e){
    if(st){ st.style.color='#ff7777'; st.textContent=t('correct.err')+e.message; }
    toast(t('correct.err')+e.message, 'err');
  }finally{ correctMotionBusy=false; const b=$('correct-motion'); if(b) b.disabled=false; hideOverlay(); }
}

// ids des controles spatiaux (Pos/Echelle/Opacite/Deplacer) + temporels
const BG_CTRL_IDS=['bg-on','bg-move','bg-x','bg-y','bg-z','bg-s','bg-o','bg-remove'];

function buildBillboard(){
  if(!DATA.frames || DATA.frames.length===0){
    bg=null; bgTex=[];
    BG_CTRL_IDS.forEach(id=>{const e=$(id); if(e) e.disabled=true;});
    syncBGTimeFields();
    return;
  }
  BG_CTRL_IDS.forEach(id=>{const e=$(id); if(e) e.disabled=false;});
  const aspect = (DATA.frame_w||640)/(DATA.frame_h||360);
  const h = 2.4, w = h*aspect;
  // plan vidéo au FORMAT ORIGINAL (pas d extension) ; depthTest:false + renderOrder:-1
  // empechent le sol de la couper/cacher quand on la descend.
  const geo = new THREE.PlaneGeometry(w, h);
  const mat = new THREE.MeshBasicMaterial({transparent:true, opacity:1.0,
    side:THREE.DoubleSide, depthWrite:false, depthTest:false});
  bg = new THREE.Mesh(geo, mat);
  bg.up.set(0,0,1);
  // use UI-field defaults as source of truth (Pos X/Y/Z, Scale, Opacity)
  const _bgX = parseFloat($('bg-x').value)||0;
  const _bgY = parseFloat($('bg-y').value)||0;
  const _bgZ = parseFloat($('bg-z').value)||0;
  const _bgS = parseFloat($('bg-s').value)||0.5;
  const _bgO = parseFloat($('bg-o').value); const bgOp = isFinite(_bgO)?_bgO:1.0;
  bg.scale.set(_bgS,_bgS,_bgS);
  bg.position.set(_bgX, _bgY, _bgZ);
  bg.material.opacity = bgOp;
  bg.rotation.x = Math.PI/2;
  bg.renderOrder = -1;
  bg.userData.isBG = true;
  scene.add(bg);
  bgTex = new Array(DATA.frames.length).fill(null);
  bgSegCache = new Array(DATA.frames.length).fill(null);
  // reset "Remove background" checkbox (material is fresh MeshBasicMaterial)
  if($('bg-remove')) $('bg-remove').checked = false;
  syncBGFields();
  syncBGTimeFields();
}

// borne max du slider temporel = video_duration - clip_duration (0 si inconnu)
function bgTimeMax(){
  const vd=DATA && DATA.video_duration, cd=DATA && DATA.clip_duration;
  if(vd==null || cd==null) return 0;
  return Math.max(0, vd - cd);
}

// synchronise le slider + champ numerique « Instant vidéo (s) » avec
// DATA.bg_offset et les bornes du clip courant. Desactive si pas de duree connue.
function syncBGTimeFields(){
  const sl=$('bg-t'), num=$('bg-t-num');
  if(!sl || !num) return;
  const hasVideo = !!(bg && DATA && DATA.frames && DATA.frames.length);
  const max=bgTimeMax();
  const off=(DATA && DATA.bg_offset!=null)?DATA.bg_offset:0;
  const known=hasVideo && DATA.video_duration!=null && DATA.clip_duration!=null;
  sl.min=0; sl.max=max.toFixed(2); sl.step=0.1;
  num.min=0; num.max=max.toFixed(2); num.step=0.1;
  const v=Math.max(0,Math.min(off,max));
  sl.value=v; num.value=v.toFixed(2);
  // pas de duree fiable -> on laisse le champ visible mais inerte
  ['bg-t','bg-t-num','bg-t-m2','bg-t-m05','bg-t-p05','bg-t-p2','bg-reextract']
    .forEach(id=>{const e=$(id); if(e) e.disabled=!known;});
}

// lit l'instant courant du champ (slider/num), borne [0, max]
function bgTimeVal(){
  const max=bgTimeMax();
  if(!$('bg-t-num')) return 0;
  let v=parseFloat($('bg-t-num').value);
  if(!isFinite(v)) v=0;
  return Math.max(0,Math.min(v,max));
}
function setBGTimeVal(v){
  const max=bgTimeMax();
  v=Math.max(0,Math.min(v,max));
  if(!$('bg-t')) return;
  $('bg-t').value=v; $('bg-t-num').value=v.toFixed(2);
}

// POST /set_bg_offset puis recharge les textures du fond (vide bgTex + recharge
// la frame courante). Le reglage temporel est INDEPENDANT des contrôles spatiaux
// (Pos/Echelle/Opacite ne sont pas touches).
async function reextractBg(){
  if(!CLIP_NAME){ return; }
  if(!(DATA && DATA.video_duration!=null && DATA.clip_duration!=null)){
    $('bg-t-status').textContent='✗ '+t('bg.time.novideo');
    $('bg-t-status').style.color='#ff7777'; return;
  }
  const off=bgTimeVal();
  const st=$('bg-t-status');
  st.style.color='#9aa0ac'; st.textContent='⏳ '+t('bg.time.extracting');
  $('bg-reextract').disabled=true;
  try{
    const r=await fetch(`/set_bg_offset?clip=${encodeURIComponent(CLIP_NAME)}&offset_s=${off}`,
      {method:'POST'});
    if(!r.ok) throw new Error(await errMsg(r));
    const res=await r.json();
    // met a jour DATA (offset effectif borne + frames eventuellement renouvelees)
    DATA.bg_offset=res.offset_sec;
    if(res.frames) DATA.frames=res.frames;
    if(res.frame_w) DATA.frame_w=res.frame_w;
    if(res.frame_h) DATA.frame_h=res.frame_h;
    // vide le cache de textures et force le rechargement de la frame courante
    bgTex=new Array(DATA.frames.length).fill(null);
    for(const tx of bgSegCache){ tx?.dispose?.(); }
    bgSegCache=new Array(DATA.frames.length).fill(null);
    if(bg){ setBGMap(null); }
    bgVersion=res.bg_version||Date.now();   // anti-cache navigateur
    loadFrameTex(curFrame);
    setBGTimeVal(res.offset_sec);
    st.style.color='#7fd18b';
    st.textContent='✓ '+t('bg.time.done')+` (${res.offset_sec.toFixed(2)} s)`;
  }catch(err){
    st.style.color='#ff7777'; st.textContent='✗ '+err.message;
  }finally{
    $('bg-reextract').disabled=false;
  }
}

// POST /bundle/set_media : importe ou remplace la vidéo de fond OU la musique
// du clip courant, puis rafraichit l'affichage par le MEME chemin que la
// ré-extraction (vidéo) ou setMusicSrc (musique). kind = 'video' | 'music'.
async function importMedia(kind){
  if(!CLIP_NAME) return;
  const fileEl=$(kind==='video'?'bg-import-video-file':'bg-import-music-file');
  const st=$(kind==='video'?'bg-import-video-status':'bg-import-music-status');
  const btn=$(kind==='video'?'bg-import-video':'bg-import-music');
  const file=fileEl && fileEl.files && fileEl.files[0];
  if(!file){ st.style.color='#ff7777'; st.textContent='✗ '+t('bg.import.nofile'); return; }
  const fd=new FormData(); fd.append('file', file);
  st.style.color='#9aa0ac'; st.textContent='⏳ '+t('bg.import.uploading');
  if(btn) btn.disabled=true;
  try{
    const r=await fetch(`/bundle/set_media?name=${encodeURIComponent(CLIP_NAME)}&kind=${kind}`,
      {method:'POST', body:fd});
    if(!r.ok) throw new Error(await errMsg(r));
    const res=await r.json();
    if(kind==='video'){
      // meme chemin que reextractBg : maj DATA + rebuild billboard + reset caches.
      DATA.has_video=true;
      if(res.frames) DATA.frames=res.frames;
      if(res.frame_w) DATA.frame_w=res.frame_w;
      if(res.frame_h) DATA.frame_h=res.frame_h;
      if(res.video_duration!=null) DATA.video_duration=res.video_duration;
      if(res.clip_duration!=null) DATA.clip_duration=res.clip_duration;
      if(res.bg_offset!=null) DATA.bg_offset=res.bg_offset;
      if(res._clip_dir) CLIP=res._clip_dir;
      bgVersion=res.bg_version||Date.now();        // anti-cache navigateur
      // retire l'ancien plan de fond puis le reconstruit avec les nouvelles
      // frames (vide aussi bgTex/bgSegCache, cf. buildBillboard).
      if(bg){ scene.remove(bg); bg.geometry?.dispose?.(); bg.material?.dispose?.(); bg=null; }
      for(const tx of bgTex){ tx?.dispose?.(); }
      for(const tx of bgSegCache){ tx?.dispose?.(); }
      buildBillboard();
      loadFrameTex(curFrame);
      st.style.color='#7fd18b'; st.textContent='✓ '+t('bg.import.video.done');
    }else{
      // musique : recharge l'<audio> via le chemin existant et active le toggle.
      DATA.has_music=true;
      setMusicSrc();
      st.style.color='#7fd18b'; st.textContent='✓ '+t('bg.import.music.done');
    }
  }catch(err){
    st.style.color='#ff7777'; st.textContent='✗ '+t('bg.import.fail')+err.message;
  }finally{
    if(btn) btn.disabled=false;
  }
}

// helper : applique une texture au materiau bg, qu'il soit MeshBasicMaterial
// ou ShaderMaterial (keying "Remove background").
function setBGMap(tex){
  if(!bg) return;
  if(bg.material.uniforms && bg.material.uniforms.map !== undefined){
    bg.material.uniforms.map.value = tex;
  } else {
    bg.material.map = tex;
  }
  bg.material.needsUpdate = true;
}

function loadFrameTex(t){
  if(!bg || !DATA.frames || t>=DATA.frames.length) return;
  const bgRemoveOn = $('bg-remove') && $('bg-remove').checked;
  // Si bg-remove est actif : on prefere la texture masquee par le SERVEUR
  // (cache front bgSegCache[t]), sinon on l'affiche brut le temps que le
  // serveur reponde, puis on declenche le fetch /bg_nobg.
  if(bgRemoveOn){
    if(bgSegCache[t]){
      _applySegTex(bgSegCache[t]);
      return;
    }
    // pas encore de masque : montre la frame brute en attendant et fetch serveur
    if(bgTex[t]) setBGMap(bgTex[t]);
    _segSetStatus('serveur…');
    if(!_serverNoBgFailed){
      _loadServerNoBg(t);
    } else if(_segFailed){
      _applyBGRemoveFallback(true);
    } else {
      if(!_segReady) _initSegmenter();
      _triggerSegmentation(t);
    }
    if(bgTex[t]) return;          // brut deja affiche ; le fetch chargera le masque
    // sinon on charge aussi la frame brute ci-dessous (fallback d'affichage)
  }
  if(bgTex[t]) { setBGMap(bgTex[t]); return; }
  const loader = new THREE.TextureLoader();
  // bgVersion : casse le cache navigateur apres une ré-extraction (les PNG du
  // fond sont reecrits a la meme URL).
  const bust = bgVersion ? `?v=${bgVersion}` : '';
  loader.load(`${CLIP}/${DATA.frames[t]}${bust}`, tex=>{
    tex.colorSpace = THREE.SRGBColorSpace;
    bgTex[t]=tex;
    if(bg && curFrame===t){
      const removeOn = $('bg-remove') && $('bg-remove').checked;
      if(removeOn && bgSegCache[t]){
        _applySegTex(bgSegCache[t]);
      } else {
        setBGMap(tex);   // affiche brut (le masque serveur arrivera via _loadServerNoBg)
      }
    }
  });
}

function centroid(){
  let x=0,y=0,z=0,c=0;
  for(let n=0;n<N;n++){ const b=idx(n,0,0); x+=joints[b];y+=joints[b+1];z+=joints[b+2];c++; }
  return new THREE.Vector3(x/c,y/c,z/c);
}

// ---- frame / scrub ----
// ====================================================================
//  Musique du clip — synchronisee a la timeline (GET /music)
//  L'<audio> tourne en parallele de la boucle d'images. La frame fait
//  foi : audio.currentTime = curFrame / fps. Play/pause/scrub gardent
//  son et image coherents (tolerance ~1 frame, pas sample-perfect).
// ====================================================================
function fpsVal(){ return (DATA && DATA.fps) || 30; }
function frameToSec(f){ return f / fpsVal(); }

// (re)pointe l'<audio> sur la musique du clip courant, ou le coupe si absent.
function setMusicSrc(){
  const au=$('music'); const btn=$('music-toggle');
  if(!au) return;
  const hasMusic = !!(DATA && DATA.has_music);
  if(hasMusic){
    const src=`/music?clip=${encodeURIComponent(CLIP_NAME||DATA.name)}`+
      `&source=${encodeURIComponent(CLIP_SOURCE||'original')}`;
    au.loop=true;            // boucle le son avec la vidéo (sinon il se coupe au rebouclage)
    au.src=src; au.load();
    if(btn) btn.disabled=false;
  }else{
    au.removeAttribute('src'); au.load();
    if(btn){ btn.disabled=true; }
    musicEnabled=false;
  }
  updateMusicBtn();
  au.muted = !musicEnabled;
}
function updateMusicBtn(){
  const btn=$('music-toggle'); if(!btn) return;
  const hasMusic=!!(DATA && DATA.has_music);
  if(!hasMusic){ btn.textContent='🔇'; btn.title=t('music.none'); return; }
  btn.textContent = musicEnabled ? '🔊' : '🔇';
  btn.title = t(musicEnabled ? 'music.on' : 'music.muted');
}
// aligne l'audio sur la frame courante (scrub / saut de frame).
function syncMusicToFrame(){
  const au=$('music'); if(!au || !(DATA && DATA.has_music)) return;
  const target=frameToSec(curFrame);
  // ne re-seek que si l'ecart depasse ~1 frame (evite les micro-coupures).
  if(Math.abs((au.currentTime||0)-target) > 1.5/fpsVal()){
    try{ au.currentTime=target; }catch(e){}
  }
}
// lance/arrete l'audio avec la lecture (appele depuis le toggle play).
function syncMusicPlayback(){
  const au=$('music'); if(!au || !(DATA && DATA.has_music)) return;
  au.muted=!musicEnabled;
  if(playing){
    syncMusicToFrame();
    const p=au.play(); if(p && p.catch) p.catch(()=>{});  // autoplay bloque -> ignore
  }else{
    au.pause();
  }
}
function toggleMusic(){
  if(!(DATA && DATA.has_music)) return;
  musicEnabled=!musicEnabled;
  const au=$('music'); if(au) au.muted=!musicEnabled;
  updateMusicBtn();
  if(playing) syncMusicPlayback();
}

function setFrame(t){
  curFrame = Math.max(0, Math.min(T-1, t|0));
  for(let n=0;n<N;n++){
    const d=dancers[n];
    const arr=d.posAttr.array;
    for(let j=0;j<J;j++){
      const b=idx(n,curFrame,j);
      d.spheres[j].position.set(edited[b],edited[b+1],edited[b+2]);
      arr[j*3]=edited[b]; arr[j*3+1]=edited[b+1]; arr[j*3+2]=edited[b+2];
    }
    d.posAttr.needsUpdate=true;
    // chemin REFIT : verts deja en memoire (DATA._verts), pas de fetch.
    if(!meshLive && meshObjs[n] && DATA._verts){
      const V=DATA._V; const pos=meshObjs[n].geometry.attributes.position.array;
      const base=((n*T+curFrame)*V)*3;
      pos.set(DATA._verts.subarray(base, base+V*3));
      meshObjs[n].geometry.attributes.position.needsUpdate=true;
      meshObjs[n].geometry.computeVertexNormals();
    }
  }
  // chemin LIVE : verts de la frame courante a la demande.
  if(meshLive && meshVisible()){
    // danseurs en TRANSLATION PURE : base + offset, instantane (jamais refites).
    const rigids={};
    for(let n=0;n<N;n++){ const r=dancerRigidOffset(n); if(r.rigid && r.edits) rigids[n]=r.off; }
    if(Object.keys(rigids).length) applyRigidLiveFrame(curFrame, rigids);
    if(playing){
      // lecture : si en cache -> applique tout de suite (pas de debounce, le maillage
      // s'anime). Sinon on garde la derniere pose et on laisse la pompe rattraper.
      if(meshCache.has(curFrame)){
        const v=meshCache.get(curFrame); cacheMeshFrame(curFrame,v); applyMeshVerts(v);
        if(Object.keys(rigids).length) applyRigidLiveFrame(curFrame, rigids);
      }
      pumpMeshPrefetch();
    }else{
      // scrub : comportement historique (debounce, fetch de la frame stabilisee).
      requestMeshFrame(curFrame, false);
    }
  }
  // prechargement du fond (crop) devant la tete de lecture, comme le maillage.
  if(playing && bgPrefetchOn) pumpBgPrefetch();
  // fantome « avant » : verts d'origine de la frame courante (pre-edition).
  if(ghostOn && ghostObjs.length) updateGhostFrame(curFrame);
  loadFrameTex(curFrame);
  $('fid').textContent=curFrame; $('frame').value=curFrame;
  refreshFloorDist();
  updateJointFields();
  if(stretchMode && typeof renderStretchPanel==='function') renderStretchPanel();
  attachGizmo();
  // synchro audio : en scrub (pas en lecture) on recale l'audio sur la frame.
  // En lecture, c'est l'audio qui avance librement -> pas de re-seek ici.
  if(!playing) syncMusicToFrame();
}

// ---- selection / gizmo ----
function attachGizmo(){
  if(floorEditMode){ if(floorGrid && tcontrols.object!==floorGrid) tcontrols.attach(floorGrid); return; }
  if(bgMoveMode && bg){ tcontrols.setMode('translate'); tcontrols.attach(bg); return; }
  if(dancerMoveMode){
    const b=idx(selDancer,curFrame,0);
    dancerProxy.position.set(edited[b],edited[b+1],edited[b+2]);
    proxyLastPos.copy(dancerProxy.position);
    tcontrols.setMode('translate');
    tcontrols.attach(dancerProxy);
    return;
  }
  const m = dancers[selDancer]?.spheres[selJoint];
  if(m) tcontrols.attach(m);
}

// translate les 24 joints du danseur selectionne d'un delta.
function moveDancer(dx,dy,dz,allFrames){
  const n=selDancer;
  const frames = allFrames ? Array.from({length:T},(_,t)=>t) : [curFrame];
  for(const t of frames){
    for(let j=0;j<J;j++){
      const b=idx(n,t,j);
      edited[b]+=dx; edited[b+1]+=dy; edited[b+2]+=dz;
    }
  }
  refreshDancerVisual(n);
  updateJointFields();
}

// moveDancer + push une commande undo (geste utilisateur via boutons ±)
function moveDancerCmd(dx,dy,dz){
  if(stretchMode){
    // mode etirement : la CIBLE du bassin a la frame courante = position bassin actuelle + delta
    const n=selDancer;
    const b=idx(n,curFrame,0);
    stretchSetPtCmd(n,curFrame, edited[b]+dx, edited[b+1]+dy, edited[b+2]+dz);
    return;
  }
  const allFrames=$('move-all').checked;
  moveDancer(dx,dy,dz,allFrames);
  pushCmd({type:'move', n:selDancer, dx,dy,dz, allFrames, frames:[curFrame]});
  bumpStepper(dx,dy,dz);
}

function refreshDancerVisual(n){
  const d=dancers[n]; const arr=d.posAttr.array;
  for(let j=0;j<J;j++){
    const b=idx(n,curFrame,j);
    d.spheres[j].position.set(edited[b],edited[b+1],edited[b+2]);
    arr[j*3]=edited[b]; arr[j*3+1]=edited[b+1]; arr[j*3+2]=edited[b+2];
  }
  d.posAttr.needsUpdate=true;
}

// ====================================================================
//  Etirement du deplacement (points cibles du bassin)
//  stretchOffset(n,t) : offset rigide (par axe) qui etire le deplacement original
//    entre les points cibles, ancre au 1er point, queue constante apres le dernier.
//  recomposeDancer(n) : edited[n] = joints[n] + stretchOffset(n,t) sur tout (N,T,J).
// ====================================================================
// position ORIGINALE du bassin du danseur n a la frame t (par axe : 0=X,1=Y,2=Z)
function pelvisOrig(n,t,axis){ return joints[idx(n,t,0)+axis]; }
// offset rigide [ox,oy,oz] applique a tous les joints du danseur n a la frame t.
function stretchOffset(n,t){
  const ps=stretchPts[n];
  if(!ps || !ps.length) return [0,0,0];
  const out=[0,0,0];
  const first=ps[0], last=ps[ps.length-1];
  // avant le 1er point : inchange (offset 0)
  if(t<=first.f) return [0,0,0];
  // a partir du dernier point : queue constante = continuite
  if(t>=last.f){
    return [ last.x-pelvisOrig(n,last.f,0),
             last.y-pelvisOrig(n,last.f,1),
             last.z-pelvisOrig(n,last.f,2) ];
  }
  // points encadrants i,i+1 : f_i <= t < f_{i+1}
  let i=0;
  for(let k=0;k<ps.length-1;k++){ if(t>=ps[k].f && t<ps[k+1].f){ i=k; break; } }
  const pi=ps[i], pj=ps[i+1];
  const piPos=[pi.x,pi.y,pi.z], pjPos=[pj.x,pj.y,pj.z];
  for(let a=0;a<3;a++){
    const oi=pelvisOrig(n,pi.f,a), oj=pelvisOrig(n,pj.f,a), ot=pelvisOrig(n,t,a);
    const denom=oj-oi;
    let nw;
    if(Math.abs(denom)>1e-6){
      // etirement proportionnel : preserve la forme du mouvement original
      nw = piPos[a] + (ot-oi)*(pjPos[a]-piPos[a])/denom;
    } else {
      // pas de mouvement original sur cet axe -> rampe lineaire d'offset
      const u=(t-pi.f)/((pj.f-pi.f)||1);
      const offI=piPos[a]-oi, offJ=pjPos[a]-oj;
      nw = ot + offI + u*(offJ-offI);
    }
    out[a]=nw-ot;
  }
  return out;
}
// recompose edited pour le danseur n depuis sa base joints + etirement.
// NOTE : ecrase les eventuelles editions par-joint de CE danseur (cf. limites).
function recomposeDancer(n){
  for(let t=0;t<T;t++){
    const off=stretchOffset(n,t);
    for(let j=0;j<J;j++){ const b=idx(n,t,j);
      edited[b]=joints[b]+off[0]; edited[b+1]=joints[b+1]+off[1]; edited[b+2]=joints[b+2]+off[2]; }
  }
}
// trouve l'index d'un point a la frame f (ou -1)
function stretchPtIndexAt(n,f){ const ps=stretchPts[n]; if(!ps) return -1;
  for(let i=0;i<ps.length;i++) if(ps[i].f===f) return i; return -1; }
// pose/maj un point cible {f,x,y,z} dans la liste triee du danseur n
function stretchUpsertPt(n,f,x,y,z){
  if(!stretchPts[n]) stretchPts[n]=[];
  const ps=stretchPts[n]; const i=stretchPtIndexAt(n,f);
  if(i>=0){ ps[i].x=x; ps[i].y=y; ps[i].z=z; }
  else { ps.push({f,x,y,z}); ps.sort((a,b)=>a.f-b.f); }
}
// snapshot profond des points d'un danseur (pour undo)
function stretchSnapshot(n){ return (stretchPts[n]||[]).map(p=>({f:p.f,x:p.x,y:p.y,z:p.z})); }
function stretchRestore(n,snap){ stretchPts[n]=snap.map(p=>({f:p.f,x:p.x,y:p.y,z:p.z})); }
// pose un point cible a la frame courante (cible absolue donnee) en commande undo.
function stretchSetPtCmd(n,f,x,y,z){
  const before=stretchSnapshot(n);
  stretchUpsertPt(n,f,x,y,z);
  const after=stretchSnapshot(n);
  recomposeDancer(n);
  pushCmd({type:'stretch', n, before, after});
  refreshDancerVisual(n); setFrame(curFrame); renderStretchPanel();
}

// ---- gizmo drag : capture la position au debut, 1 commande a la fin ----
function onDraggingChanged(e){
  orbit.enabled = !e.value;
  const obj=tcontrols.object;
  if(e.value){           // debut de drag
    draggingGizmo=true;
    if(obj) dragStartPos.copy(obj.position);
    // mode etirement : memorise l'etat des points pour fabriquer une commande undo au relachement
    if(stretchMode && obj===dancerProxy) stretchDragSnap=stretchSnapshot(selDancer);
  } else {               // fin de drag -> pousse 1 commande undo
    draggingGizmo=false;
    if(!obj || obj.userData?.isBG || obj.userData?.isFloor) return;
    if(obj===dancerProxy){
      const dx=obj.position.x-dragStartPos.x, dy=obj.position.y-dragStartPos.y, dz=obj.position.z-dragStartPos.z;
      if(stretchMode){
        // un seul point cible a la frame courante a ete pose/maj pendant le drag
        if(dx||dy||dz){
          const after=stretchSnapshot(selDancer);
          pushCmd({type:'stretch', n:selDancer, before:stretchDragSnap||[], after});
          renderStretchPanel();
        }
        stretchDragSnap=null;
      } else if(dx||dy||dz){ pushCmd({type:'move', n:selDancer, dx,dy,dz, allFrames:$('move-all').checked, frames:[curFrame]});
        bumpStepper(dx,dy,dz); }
    } else {
      const {n,j}=obj.userData;
      const before=[dragStartPos.x,dragStartPos.y,dragStartPos.z];
      const after=[obj.position.x,obj.position.y,obj.position.z];
      if(before[0]!==after[0]||before[1]!==after[1]||before[2]!==after[2])
        pushCmd({type:'joint', n, t:curFrame, j, before, after});
    }
  }
}

function onGizmoMove(){
  const obj = tcontrols.object;
  if(!obj) return;
  if(obj.userData.isFloor){ onFloorGizmo(); return; }
  if(obj.userData.isBG){ syncBGFields(); return; }
  if(obj===dancerProxy){
    const dx=obj.position.x-proxyLastPos.x;
    const dy=obj.position.y-proxyLastPos.y;
    const dz=obj.position.z-proxyLastPos.z;
    proxyLastPos.copy(obj.position);
    if(dx||dy||dz){
      if(stretchMode){
        // live : la cible du bassin a la frame courante = position absolue du gizmo
        const n=selDancer;
        stretchUpsertPt(n,curFrame, obj.position.x, obj.position.y, obj.position.z);
        recomposeDancer(n); refreshDancerVisual(n);
        if(typeof renderStretchPanel==='function') renderStretchPanel();
      } else {
        moveDancer(dx,dy,dz,$('move-all').checked);
      }
    }
    return;
  }
  const {n,j} = obj.userData;
  const b=idx(n,curFrame,j);
  edited[b]=obj.position.x; edited[b+1]=obj.position.y; edited[b+2]=obj.position.z;
  const arr=dancers[n].posAttr.array;
  arr[j*3]=obj.position.x; arr[j*3+1]=obj.position.y; arr[j*3+2]=obj.position.z;
  dancers[n].posAttr.needsUpdate=true;
  if(n===selDancer && j===selJoint) updateJointFields();
}

function pick(ev){
  if(bgMoveMode || floorEditMode) return;
  const r=renderer.domElement.getBoundingClientRect();
  pointer.x=((ev.clientX-r.left)/r.width)*2-1;
  pointer.y=-((ev.clientY-r.top)/r.height)*2+1;
  raycaster.setFromCamera(pointer,camera);
  const all=[]; dancers.forEach(d=>all.push(...d.spheres));
  const hit=raycaster.intersectObjects(all,false);
  if(hit.length){
    const {n,j}=hit[0].object.userData;
    selDancer=n;
    if(!dancerMoveMode) selJoint=j;
    $('sel-d').value=n; $('sel-j').value=selJoint; updateSwatch();
    attachGizmo(); updateJointFields(); syncGlobalFields();
    if(stretchMode) renderStretchPanel();
  }
}

function updateJointFields(){
  const b=idx(selDancer,curFrame,selJoint);
  $('j-x').value=edited[b].toFixed(3);
  $('j-y').value=edited[b+1].toFixed(3);
  $('j-z').value=edited[b+2].toFixed(3);
}

function applyJointFields(){
  const b=idx(selDancer,curFrame,selJoint);
  const before=[edited[b],edited[b+1],edited[b+2]];
  const after=[parseFloat($('j-x').value)||0, parseFloat($('j-y').value)||0, parseFloat($('j-z').value)||0];
  edited[b]=after[0]; edited[b+1]=after[1]; edited[b+2]=after[2];
  if(before[0]!==after[0]||before[1]!==after[1]||before[2]!==after[2])
    pushCmd({type:'joint', n:selDancer, t:curFrame, j:selJoint, before, after});
  setFrame(curFrame);
}

function syncBGFields(){
  if(!bg) return;
  $('bg-x').value=bg.position.x.toFixed(3);
  $('bg-y').value=bg.position.y.toFixed(3);
  $('bg-z').value=bg.position.z.toFixed(3);
  $('bg-s').value=bg.scale.x.toFixed(3);
  const _op = (bg.material.uniforms && bg.material.uniforms.opacity !== undefined)
    ? bg.material.uniforms.opacity.value : bg.material.opacity;
  $('bg-o').value=_op.toFixed(2);
}

// ---- Remove Background : segmentation ML (MediaPipe Tasks-Vision) ----
// Utilise ImageSegmenter (modèle selfie_segmenter_landscape) chargé depuis le CDN
// jsDelivr. Pour chaque frame : segmente → canvas RGBA (personnes=opaque,fond=alpha 0)
// → texture Three.js mise en cache dans bgSegCache[t].
// Fallback gracieux : si le CDN/modèle est inaccessible, retombe sur un keying simple
// par luminance (identique à l'ancien comportement).
//
// Variables d'état du segmenteur :
//   _segReady      : true quand ImageSegmenter est prêt
//   _segFailed     : true si le chargement a échoué (→ fallback keying)
//   _segmenter     : instance ImageSegmenter
//   _segPending    : Set des indices de frame en cours de segmentation (évite doublons)
let _segReady = false;
let _segFailed = false;
let _segmenter = null;
let _segPending = new Set();

// CDN : on charge le bundle ES-module de @mediapipe/tasks-vision depuis jsDelivr.
// Le modèle wasm + .task sont également tirés du même CDN.
const _MEDIAPIPE_CDN = 'https://cdn.jsdelivr.net/npm/@mediapipe/tasks-vision@0.10.14/wasm';
const _MEDIAPIPE_PKG = 'https://cdn.jsdelivr.net/npm/@mediapipe/tasks-vision@0.10.14';
const _SEG_MODEL_URL  = `${_MEDIAPIPE_PKG}/models/selfie_segmenter_landscape.tflite`;

function _segSetStatus(msg){
  const el = $('bg-seg-status');
  if(el) el.textContent = msg;
}

// ====================================================================
//  Remove Background — chemin PRINCIPAL : segmentation COTE SERVEUR.
//  Le serveur calcule un masque de personnes sur GPU (deeplabv3) et
//  renvoie un PNG RGBA (fond transparent) via GET /bg_nobg. On charge
//  ce PNG comme texture du plan video. Bien plus robuste que la
//  segmentation selfie du navigateur sur les scenes multi-danseurs.
//  Cache cote serveur (disque) + cache cote front (bgSegCache[t]).
//  Fallback : si l'endpoint echoue, on retombe sur la segmentation
//  navigateur (MediaPipe) puis sur le keying par luminance.
// ====================================================================
let _serverNoBgFailed = false;        // true si /bg_nobg a echoue (-> fallback navigateur)
let _serverNoBgPending = new Set();   // frames en cours de fetch serveur

// URL du PNG masque cote serveur pour la frame t.
function _serverNoBgUrl(t){
  const clip = encodeURIComponent(CLIP_NAME || (DATA && DATA.name) || '');
  const src  = encodeURIComponent(CLIP_SOURCE || 'original');
  const bust = bgVersion ? `&v=${bgVersion}` : '';
  return `/bg_nobg?clip=${clip}&source=${src}&frame=${t}${bust}`;
}

// Charge le PNG masque (serveur) de la frame t en texture, le met en cache
// dans bgSegCache[t] et l'applique si on est toujours sur cette frame.
// En cas d'echec : bascule sur la segmentation navigateur (fallback).
function _loadServerNoBg(t){
  if(bgSegCache[t] || _serverNoBgPending.has(t)) return;
  if(!DATA || !DATA.frames || t >= DATA.frames.length) return;
  _serverNoBgPending.add(t);
  setLoadHud('bg', true);   // au moins un fetch de fond en vol
  const loader = new THREE.TextureLoader();
  loader.load(
    _serverNoBgUrl(t),
    tex => {
      _serverNoBgPending.delete(t);
      tex.colorSpace = THREE.SRGBColorSpace;
      if(bgSegCache[t]) bgSegCache[t].dispose();
      bgSegCache[t] = tex;
      if(curFrame === t && $('bg-remove') && $('bg-remove').checked){
        _applySegTex(tex);
        _segSetStatus('serveur ✓');
      }
      // re-arme la pompe de prechargement du fond (lecture) + maj du HUD.
      if(bgPrefetchOn) pumpBgPrefetch();
      else setLoadHud('bg', _serverNoBgPending.size>0);
    },
    undefined,
    err => {
      _serverNoBgPending.delete(t);
      setLoadHud('bg', _serverNoBgPending.size>0);
      console.warn('[bg-remove] /bg_nobg a echoue, fallback navigateur:', err);
      _serverNoBgFailed = true;
      _segSetStatus('fallback navigateur…');
      // Bascule sur le chemin navigateur (MediaPipe / luma) pour cette frame.
      if(_segFailed){
        _applyBGRemoveFallback(true);
      } else {
        if(!_segReady) _initSegmenter();
        _triggerSegmentation(t);
      }
    }
  );
}

// Charge le module @mediapipe/tasks-vision de façon dynamique (import() depuis CDN).
// Résout avec l'instance ImageSegmenter ou lève une exception.
async function _loadSegmenter(){
  _segSetStatus('chargement modèle…');
  // Import dynamique du module ES depuis le CDN
  const mod = await import(`${_MEDIAPIPE_PKG}/vision_bundle.mjs`);
  const { ImageSegmenter, FilesetResolver } = mod;
  const vision = await FilesetResolver.forVisionTasks(_MEDIAPIPE_CDN);
  const seg = await ImageSegmenter.createFromOptions(vision, {
    baseOptions: {
      modelAssetPath: _SEG_MODEL_URL,
      delegate: 'GPU',          // GPU si dispo, sinon CPU auto
    },
    runningMode: 'IMAGE',
    outputCategoryMask: false,
    outputConfidenceMasks: true,   // masque float 0-1 pour la personne
  });
  return seg;
}

// Initialise le segmenteur en arrière-plan.
async function _initSegmenter(){
  if(_segReady || _segFailed) return;
  try {
    _segmenter = await _loadSegmenter();
    _segReady = true;
    _segSetStatus('ML ✓');
    console.log('[bg-remove] MediaPipe segmenter ready');
    // Si la checkbox est active, re-déclenche la segmentation de la frame courante
    if($('bg-remove').checked) _triggerSegmentation(curFrame);
  } catch(err) {
    _segFailed = true;
    _segSetStatus('fallback');
    console.warn('[bg-remove] MediaPipe load failed, fallback to luma keying:', err);
    // Si la checkbox est déjà cochée, active le keying fallback
    if($('bg-remove').checked) _applyBGRemoveFallback(true);
  }
}

// Segmente la frame t de façon asynchrone, met le résultat dans bgSegCache[t],
// puis met à jour la texture si on est toujours sur cette frame.
async function _triggerSegmentation(t){
  if(_segPending.has(t) || bgSegCache[t]) return;
  if(!DATA || !DATA.frames || t >= DATA.frames.length) return;
  _segPending.add(t);
  try {
    // 1. Charge l'image source dans un HTMLImageElement
    const img = await new Promise((res, rej) => {
      const im = new Image();
      im.crossOrigin = 'anonymous';
      const bust = bgVersion ? `?v=${bgVersion}` : '';
      im.onload = () => res(im);
      im.onerror = rej;
      im.src = `${CLIP}/${DATA.frames[t]}${bust}`;
    });

    // 2. Segmente avec MediaPipe
    const result = _segmenter.segment(img);
    // result.confidenceMasks[0] = WebGLTexture ou MPMask pour la "personne"
    // On le tire en Float32Array via getAsFloat32Array()
    const mask = result.confidenceMasks[0];
    const W = mask.width, H = mask.height;
    const maskData = mask.getAsFloat32Array();  // longueur = W * H, valeur [0,1]

    // 3. Compose : image RGBA × masque → canvas
    const canvas = document.createElement('canvas');
    canvas.width = img.naturalWidth; canvas.height = img.naturalHeight;
    const ctx = canvas.getContext('2d');
    ctx.drawImage(img, 0, 0);
    const imgData = ctx.getImageData(0, 0, canvas.width, canvas.height);
    const pix = imgData.data; // Uint8ClampedArray RGBA

    // Le masque peut avoir une résolution différente de l'image source
    const mW = W, mH = H, iW = canvas.width, iH = canvas.height;
    for(let py = 0; py < iH; py++){
      for(let px = 0; px < iW; px++){
        const pi = (py * iW + px) * 4;
        // Resampling nearest-neighbor si résolutions différentes
        const mx = Math.round(px * (mW - 1) / Math.max(iW - 1, 1));
        const my = Math.round(py * (mH - 1) / Math.max(iH - 1, 1));
        const conf = maskData[my * mW + mx];  // 0 = fond, 1 = personne
        pix[pi + 3] = Math.round(conf * pix[pi + 3]);
      }
    }
    ctx.putImageData(imgData, 0, 0);

    // Libère la ressource WebGL du masque
    mask.close();

    // 4. Crée la texture Three.js depuis le canvas
    const tex = new THREE.CanvasTexture(canvas);
    tex.colorSpace = THREE.SRGBColorSpace;
    if(bgSegCache[t]) bgSegCache[t].dispose();
    bgSegCache[t] = tex;

    // 5. Met à jour le rendu si on est toujours sur cette frame et que bg-remove est actif
    if(curFrame === t && $('bg-remove').checked){
      _applySegTex(tex);
    }
  } catch(err) {
    console.warn('[bg-remove] segmentation frame', t, 'failed:', err);
  } finally {
    _segPending.delete(t);
  }
}

// Applique une texture masquée (canvas) au matériau bg (MeshBasicMaterial transparent).
function _applySegTex(tex){
  if(!bg) return;
  const curOpacity = parseFloat($('bg-o').value); const op = isFinite(curOpacity)?curOpacity:1.0;
  // Si le matériau est déjà un MeshBasicMaterial transparent avec le bon réglage, on
  // se contente de changer la map. Sinon on recrée proprement.
  if(!(bg.material.isMeshBasicMaterial)){
    const oldMap = (bg.material.uniforms && bg.material.uniforms.map) ? bg.material.uniforms.map.value : bg.material.map;
    bg.material.dispose();
    bg.material = new THREE.MeshBasicMaterial({
      map: tex,
      transparent: true,
      opacity: op,
      side: THREE.DoubleSide,
      depthWrite: false,
      depthTest: false,
    });
    bg.renderOrder = -1;
  } else {
    bg.material.map = tex;
    bg.material.transparent = true;
    bg.material.opacity = op;
    bg.material.needsUpdate = true;
  }
}

// ---- Fallback : keying par luminance (ancien comportement) ----
// Activé si MediaPipe ne charge pas.
const BG_REMOVE_VERT = `
  varying vec2 vUv;
  void main(){
    vUv = uv;
    gl_Position = projectionMatrix * modelViewMatrix * vec4(position,1.0);
  }
`;
const BG_REMOVE_FRAG = `
  uniform sampler2D map;
  uniform float opacity;
  varying vec2 vUv;
  const float LUM_THRESH = 0.75;
  const float SAT_THRESH = 0.25;
  void main(){
    vec4 c = texture2D(map, vUv);
    if(c.a < 0.01){ discard; }
    float lum = dot(c.rgb, vec3(0.299, 0.587, 0.114));
    float cmax = max(c.r, max(c.g, c.b));
    float cmin = min(c.r, min(c.g, c.b));
    float sat = (lum > 0.0 && lum < 1.0) ? (cmax - cmin) / (1.0 - abs(2.0*lum - 1.0)) : 0.0;
    if(lum > LUM_THRESH && sat < SAT_THRESH){ discard; }
    gl_FragColor = vec4(c.rgb, c.a * opacity);
  }
`;
function _applyBGRemoveFallback(on){
  if(!bg) return;
  try {
    const curOpacity = parseFloat($('bg-o').value); const op = isFinite(curOpacity)?curOpacity:1.0;
    if(on){
      const currentMap = bg.material.isMeshBasicMaterial ? bg.material.map
                       : (bg.material.uniforms && bg.material.uniforms.map) ? bg.material.uniforms.map.value
                       : bg.material.map;
      bg.material.dispose();
      bg.material = new THREE.ShaderMaterial({
        uniforms:{ map:{value: currentMap}, opacity:{value: op} },
        vertexShader: BG_REMOVE_VERT,
        fragmentShader: BG_REMOVE_FRAG,
        transparent: true,
        depthTest: false,
        depthWrite: false,
        side: THREE.DoubleSide,
      });
      bg.renderOrder = -1;
    } else {
      const currentMap = (bg.material.uniforms && bg.material.uniforms.map) ? bg.material.uniforms.map.value : bg.material.map;
      bg.material.dispose();
      bg.material = new THREE.MeshBasicMaterial({
        map: currentMap,
        transparent: true,
        opacity: op,
        side: THREE.DoubleSide,
        depthWrite: false,
        depthTest: false,
      });
      bg.renderOrder = -1;
    }
    bg.material.needsUpdate = true;
  } catch(err) {
    console.warn('[bg-remove] fallback keying error:', err);
  }
}

// ---- Garde-fou : ré-applique le remove-bg sur la frame courante ----
// Après une édition/refit/correction, le matériau du fond a pu retomber sur la
// texture vidéo BRUTE (cache du masque pas encore prêt, ou matériau recréé).
// Si la case « Remove background » est cochée, on ré-applique le masque
// (cache serveur bgSegCache[curFrame] si présent, sinon on relance le fetch).
function reapplyBgRemove(){
  const cb=$('bg-remove');
  if(!bg || !cb || !cb.checked) return;
  applyBGRemove(true);
}
// ---- Point d'entrée principal : onchange de la checkbox ----
function applyBGRemove(on){
  if(!bg) return;
  if(!on){
    // Désactivation : retour au MeshBasicMaterial normal avec la texture brute
    _segSetStatus('');
    const rawTex = bgTex[curFrame] || null;
    const curOpacity = parseFloat($('bg-o').value); const op = isFinite(curOpacity)?curOpacity:1.0;
    if(!(bg.material.isMeshBasicMaterial) || bg.material.map !== rawTex){
      bg.material.dispose();
      bg.material = new THREE.MeshBasicMaterial({
        map: rawTex,
        transparent: true,
        opacity: op,
        side: THREE.DoubleSide,
        depthWrite: false,
        depthTest: false,
      });
      bg.renderOrder = -1;
    }
    bg.material.needsUpdate = true;
    return;
  }
  // Activation : chemin PRINCIPAL = segmentation cote SERVEUR (/bg_nobg).
  // Si le masque serveur de la frame courante est deja en cache, on l'applique ;
  // sinon on affiche la frame brute et on declenche le fetch serveur.
  if(bgSegCache[curFrame]){
    _applySegTex(bgSegCache[curFrame]);
    _segSetStatus('serveur ✓');
    return;
  }
  if(bgTex[curFrame]) setBGMap(bgTex[curFrame]);   // brut en attendant
  if(!_serverNoBgFailed){
    _segSetStatus('serveur…');
    _loadServerNoBg(curFrame);
    return;
  }
  // Le serveur a deja echoue auparavant : fallback navigateur (MediaPipe / luma).
  if(_segFailed){
    _applyBGRemoveFallback(true);
  } else if(_segReady){
    _segSetStatus('seg…');
    _triggerSegmentation(curFrame);
  } else {
    _segSetStatus('chargement…');
    _initSegmenter();
  }
}

// ---- steppers globaux (decalage constant cumule, PAR DANSEUR) ----
// stepCum[n]={x,y,z} : offset constant accumule du danseur n (mode "decalage constant").
// Les champs g-*-val refletent TOUJOURS le danseur courant -> syncGlobalFields() au
// changement de danseur (sel-d / clic 3D / undo-redo).
let stepCum=[];
function curStep(){ if(!stepCum[selDancer]) stepCum[selDancer]={x:0,y:0,z:0}; return stepCum[selDancer]; }
function resetStepperVals(){ stepCum[selDancer]={x:0,y:0,z:0}; renderStepperVals(); }
function bumpStepper(dx,dy,dz){ const s=curStep(); s.x+=dx; s.y+=dy; s.z+=dz; renderStepperVals(); }
function renderStepperVals(){
  const s=curStep();
  $('g-x-val').textContent=s.x.toFixed(2)+' m';
  $('g-y-val').textContent=s.y.toFixed(2)+' m';
  $('g-z-val').textContent=s.z.toFixed(2)+' m';
}
// rafraichit l'affichage des champs Largeur/Hauteur/Profond du danseur courant.
function syncGlobalFields(){ renderStepperVals(); }

// ---- panneau etirement : frise des points cibles + offset courant ----
function renderStretchPanel(){
  const box=$('stretch-box'); if(!box) return;
  box.hidden=!stretchMode;
  if($('stretch-mode')) $('stretch-mode').checked=stretchMode;
  if(!stretchMode) return;
  const n=selDancer;
  // offset applique a la frame courante
  const off=stretchOffset(n,curFrame);
  const co=$('stretch-curoff');
  if(co) co.textContent=`${t('stretch.curoff')} : X ${off[0].toFixed(2)} · Y ${off[1].toFixed(2)} · Z ${off[2].toFixed(2)} m`;
  // frise des points
  const fr=$('stretch-frieze'); if(!fr) return;
  fr.innerHTML='';
  const ps=stretchPts[n]||[];
  if(!ps.length){ const s=document.createElement('span'); s.className='small'; s.textContent=t('stretch.nopts'); fr.appendChild(s); return; }
  for(const p of ps){
    const el=document.createElement('span');
    el.className='traj-key'+(p.f===curFrame?' cur':'');
    el.textContent=`#${p.f}`;
    el.title=`${t('stretch.atframe')} ${p.f} · ${t('stretch.target')} : X ${p.x.toFixed(2)} · Y ${p.y.toFixed(2)} · Z ${p.z.toFixed(2)} m`;
    el.onclick=()=>{ setFrame(p.f); renderStretchPanel(); };
    fr.appendChild(el);
  }
}

function setStretchMode(on){
  stretchMode=!!on;
  if($('stretch-mode')) $('stretch-mode').checked=stretchMode;
  renderStretchPanel();
  attachGizmo();
}

// ====================================================================
//  Commentaires / chat PAR CLIP (GET/POST /comments). Cle = CLIP_NAME (nom de
//  base, partage entre original et corrige). Desactive pour les clips importes
//  (custom / custom_corrected). Le nom d'utilisateur est persiste (pe.user).
//  (commentsList est declare en tete avec les autres globals — TDZ.)
// ====================================================================
function commentsDisabled(){
  return CLIP_SOURCE==='custom' || CLIP_SOURCE==='custom_corrected';
}

function escapeHtml(s){
  return (s||'').replace(/[&<>"']/g, c=>(
    {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
}

function fmtCommentTime(iso){
  if(!iso) return '';
  const d=new Date(iso);
  if(isNaN(d.getTime())) return iso;
  try{ return d.toLocaleString(); }catch(_){ return iso; }
}

function renderComments(){
  const box=$('comment-list'); if(!box) return;
  box.innerHTML='';
  if(!commentsList.length){
    const e=document.createElement('div'); e.id='comment-empty';
    e.textContent=t('comments.empty'); box.appendChild(e); return;
  }
  for(const c of commentsList){
    const row=document.createElement('div'); row.className='comment-row';
    row.innerHTML=`<div class="meta"><span class="who">${escapeHtml(c.user)}</span>`+
      ` · ${escapeHtml(fmtCommentTime(c.time))}</div>`+
      `<div class="txt">${escapeHtml(c.text)}</div>`;
    box.appendChild(row);
  }
  box.scrollTop=box.scrollHeight;
}

// (de)grise l'UI commentaires selon clip importe ou non.
function syncCommentsUI(){
  const off=commentsDisabled();
  const dis=$('comment-disabled'), comp=$('comment-compose');
  if(dis) dis.style.display = off ? '' : 'none';
  if(comp) comp.style.display = off ? 'none' : '';
  const list=$('comment-list'); if(list) list.style.display = off ? 'none' : '';
}

// charge les commentaires du clip courant (sauf clips importes).
async function loadComments(){
  syncCommentsUI();
  const st=$('comment-status'); if(st) st.textContent='';
  if(!CLIP_NAME || commentsDisabled()){ commentsList=[]; renderComments(); return; }
  try{
    const r=await fetch(`/comments?clip=${encodeURIComponent(CLIP_NAME)}`);
    if(!r.ok) throw new Error(`HTTP ${r.status}`);
    const j=await r.json();
    commentsList=j.comments||[];
    // nom par defaut depuis le serveur (getpass), sauf si l'utilisatrice a deja
    // choisi/persiste un nom en localStorage.
    const ui=$('comment-user');
    if(ui && !ui.value){
      ui.value = localStorage.getItem('pe.user') || j.default_user || '';
    }
    renderComments();
  }catch(e){
    if(st){ st.style.color='#ff7777'; st.textContent=t('comments.loadfail')+e.message; }
  }
}

let commentSendBusy=false;
async function sendComment(){
  if(commentSendBusy) return;
  if(!CLIP_NAME || commentsDisabled()) return;
  const ti=$('comment-text'); const text=(ti.value||'').trim();
  if(!text) return;
  const ui=$('comment-user');
  const user=(ui && ui.value.trim()) || localStorage.getItem('pe.user') || '';
  if(ui && ui.value.trim()) localStorage.setItem('pe.user', ui.value.trim());
  const st=$('comment-status');
  commentSendBusy=true; $('comment-send').disabled=true;
  try{
    const r=await fetch(`/comments?clip=${encodeURIComponent(CLIP_NAME)}`,
      {method:'POST', headers:{'Content-Type':'application/json'},
       body:JSON.stringify({user, text})});
    if(!r.ok){ throw new Error(await errMsg(r)); }
    const j=await r.json();
    commentsList=j.comments||[];
    ti.value='';
    if(st) st.textContent='';
    renderComments();
  }catch(e){
    if(st){ st.style.color='#ff7777'; st.textContent=t('comments.sendfail')+e.message; }
  }finally{
    commentSendBusy=false; $('comment-send').disabled=false;
  }
}

function bindComments(){
  const send=$('comment-send'); if(send) send.onclick=sendComment;
  const ti=$('comment-text'); if(ti) ti.addEventListener('keydown',e=>{
    if(e.key==='Enter' && !e.shiftKey){ e.preventDefault(); sendComment(); } });
  const ui=$('comment-user');
  if(ui){
    const saved=localStorage.getItem('pe.user'); if(saved) ui.value=saved;
    ui.addEventListener('change',()=>{
      const v=ui.value.trim(); if(v) localStorage.setItem('pe.user', v); });
  }
}

// Reflète l'etat visuel (classe .on) des boutons-bascule vers aria-pressed, sans
// toucher chaque site d'appel : un observateur de mutations suffit.
function _syncTogglePressed(ids){
  ids.forEach(id=>{
    const el=$(id); if(!el) return;
    // reflète l'état .on sur aria-pressed et, pour les items de menu cochables,
    // sur aria-checked (le coche ✓ visuel vient du CSS .mb-check.on::before).
    const isCheck=el.getAttribute('role')==='menuitemcheckbox';
    const upd=()=>{ const on=el.classList.contains('on');
      el.setAttribute('aria-pressed', on?'true':'false');
      if(isCheck) el.setAttribute('aria-checked', on?'true':'false'); };
    upd();
    new MutationObserver(upd).observe(el,{attributes:true,attributeFilter:['class']});
  });
}

// ---- 1re fenêtre prête ? : 1res mailles en cache (si maillage live visible) +
//      1res frames de fond (si remove-bg actif). Sert à warmFirstFrame() (au
//      chargement du clip) pour maintenir la surcouche jusqu'à la 1re frame. ----
function _firstWindowReady(){
  // maillage : 1res frames en cache (si le maillage live est visible)
  if(meshLive && meshVisible()){
    for(let k=0;k<Math.min(MESH_PREFETCH_AHEAD,T);k++){
      if(!meshCache.has((curFrame+k)%T)) return false;
    }
  }
  // fond : 1res frames de crop en cache (si remove-bg actif et serveur OK)
  if(bgRemoveActive() && !_serverNoBgFailed){
    for(let k=0;k<Math.min(BG_PREFETCH_AHEAD,T);k++){
      if(!bgSegCache[(curFrame+k)%T]) return false;
    }
  }
  return true;
}
function togglePlay(){
  if(playing){   // pause : immediat
    playing=false; $('play').textContent='▶'; $('play').classList.remove('on');
    syncMeshPrefetch(); syncMusicPlayback();
    return;
  }
  // La 1re fenêtre a déjà été préchauffée au chargement du clip (warmFirstFrame),
  // donc la lecture démarre IMMÉDIATEMENT, sans aucune surcouche « chargement… ».
  // Le préchargement suivant continue silencieusement (syncMeshPrefetch /
  // syncBgPrefetch). Si par hasard le cache n'est pas chaud, on amorce quand
  // même les pompes : la 1re frame peut figer un instant mais aucun loader ne
  // s'affiche (UX demandée : un seul chargement, à l'ouverture).
  playing=true; $('play').textContent='❚❚'; $('play').classList.add('on');
  if(meshLive && meshVisible()){ meshPrefetchOn=true; pumpMeshPrefetch(); }
  if(bgRemoveActive() && !_serverNoBgFailed){ bgPrefetchOn=true; pumpBgPrefetch(); }
  syncMeshPrefetch(); syncMusicPlayback();
}

// ---- UI ----
function bindUI(){
  _syncTogglePressed(['t-skel','t-mesh','t-ghost','floor-on','floor-dist','play']);
  $('play').onclick=togglePlay;
  $('frame').oninput=e=>{ playing=false;$('play').textContent='▶';$('play').classList.remove('on'); syncMeshPrefetch(); setFrame(+e.target.value); };
  $('music-toggle').onclick=toggleMusic;

  $('t-skel').onclick=()=>{ if(!dancers.length) return; const v=!dancers[0].spheres[0].visible;
    dancers.forEach(d=>{d.spheres.forEach(s=>s.visible=v);d.bones.visible=v;}); $('t-skel').classList.toggle('on',v); };
  $('t-mesh').onclick=()=>{ if(!dancers.length) return; toggleMesh(); };
  $('t-ghost').onclick=()=>{ if(!dancers.length) return; toggleGhost(); };

  $('floor-on').onclick=()=>{
    if(!floorPlane && !(DATA&&DATA.floor)) return;          // aucun sol estimé du tout
    const v=!floorOnChecked(); setFloorOnChecked(v);
    if(v && !floorGrid) buildFloor();                       // (re)construit si absent
    if(floorGrid) floorGrid.visible=v; };

  $('floor-dist').onclick=()=>{ if($('floor-dist').disabled) return; setFloorDist(!floorDistOn); };

  // --- correction du sol ---
  $('floor-variant').onchange=e=>selectFloorVariant(e.target.value);
  $('floor-edit').onclick=()=>setFloorEditMode(!floorEditMode);
  ['floor-tx','floor-ty','floor-h'].forEach(id=>{ $(id).onchange=applyFloorFields; });
  $('floor-reset').onclick=()=>{ // revient au floor_corrected
    const corr=floorVariantPlane('corrected'); if(!corr) return;
    floorPlane=corr.slice(); applyPlaneToFloorMesh(floorPlane);
    updateFloorFields(); updateFloorInfo();
    $('floor-save-status').textContent='';
  };
  $('floor-save').onclick=saveFloor;
  $('floor-recompute').onclick=recomputeFloor;
  if($('correct-motion')) $('correct-motion').onclick=correctMotion;
  // si on edite le sol, sortir du mode quand on ouvre l'accordeon d'edition danseur
  $('acc-floor').addEventListener('toggle',()=>{ if(!$('acc-floor').open && floorEditMode) setFloorEditMode(false); });

  $('v-front').onclick=()=>setView('front');
  $('v-back').onclick=()=>setView('back');
  $('v-left').onclick=()=>setView('left');
  $('v-right').onclick=()=>setView('right');
  $('v-top').onclick=()=>setView('top');
  $('v-bottom').onclick=()=>setView('bottom');

  $('bg-on').onchange=e=>{ if(bg) bg.visible=e.target.checked; };
  $('bg-move').onclick=()=>{ if(!bg) return; bgMoveMode=!bgMoveMode;
    $('bg-move').classList.toggle('on',bgMoveMode); attachGizmo(); };
  ['x','y','z'].forEach(a=>{ $('bg-'+a).oninput=()=>{ if(bg) bg.position[a]=parseFloat($('bg-'+a).value)||0; }; });
  $('bg-s').oninput=e=>{ if(!bg) return; const s=parseFloat(e.target.value)||1; bg.scale.set(s,s,s); };
  $('bg-o').oninput=e=>{ if(bg) {
    const v=parseFloat(e.target.value);
    if(bg.material.uniforms && bg.material.uniforms.opacity !== undefined){
      bg.material.uniforms.opacity.value=v;
    } else { bg.material.opacity=v; }
    bg.material.needsUpdate=true;
  } };
  $('bg-remove').onchange=e=>{
    applyBGRemove(e.target.checked);
    if(e.target.checked){ prewarmBg(); syncBgPrefetch(); }   // warm serveur + prefetch lecture
    else { bgPrefetchOn=false; setLoadHud('bg', false); }
  };

  // --- import / remplacement vidéo + musique (POST /bundle/set_media) ---
  if($('bg-import-video')) $('bg-import-video').onclick=()=>importMedia('video');
  if($('bg-import-music')) $('bg-import-music').onclick=()=>importMedia('music');

  // accordeon Global / Joints : pilote dancerMoveMode (gizmo bassin vs joint)
  $('acc-global').addEventListener('toggle', onAccordion);
  $('acc-joints').addEventListener('toggle', onAccordion);

  // steppers globaux
  const stepVal=()=>parseFloat($('g-step').value)||0.01;
  $('g-x-minus').onclick=()=>moveDancerCmd(-stepVal(),0,0);
  $('g-x-plus').onclick =()=>moveDancerCmd(+stepVal(),0,0);
  $('g-z-minus').onclick=()=>moveDancerCmd(0,0,-stepVal());
  $('g-z-plus').onclick =()=>moveDancerCmd(0,0,+stepVal());
  $('g-y-minus').onclick=()=>moveDancerCmd(0,-stepVal(),0);
  $('g-y-plus').onclick =()=>moveDancerCmd(0,+stepVal(),0);
  $('g-reset').onclick=()=>{ // remet les joints du danseur a leur valeur d'origine (toutes frames)
    const n=selDancer;
    stretchPts[n]=[];   // efface aussi l'etirement de ce danseur
    for(let t=0;t<T;t++) for(let j=0;j<J;j++){ const b=idx(n,t,j);
      edited[b]=joints[b];edited[b+1]=joints[b+1];edited[b+2]=joints[b+2]; }
    resetStepperVals(); setFrame(curFrame); renderStretchPanel();
    undoStack.length=0; redoStack.length=0; refreshUndoButtons();   // reset = barriere historique
    markDirty();   // les joints different (peut-etre) du dernier pkl sauvegardé
  };

  // --- mode etirement du deplacement (points cibles du bassin) ---
  $('stretch-mode').onchange=e=>setStretchMode(e.target.checked);
  // "Ancrer ici" : point dont la cible = position ORIGINALE du bassin a cette frame (ancre fixe)
  $('stretch-anchor').onclick=()=>{ const n=selDancer;
    stretchSetPtCmd(n,curFrame, pelvisOrig(n,curFrame,0), pelvisOrig(n,curFrame,1), pelvisOrig(n,curFrame,2)); };
  // "Poser/maj le point ici" : cible = position COURANTE du bassin (apres deplacement eventuel)
  $('stretch-setpt').onclick=()=>{ const n=selDancer; const b=idx(n,curFrame,0);
    stretchSetPtCmd(n,curFrame, edited[b], edited[b+1], edited[b+2]); };
  $('stretch-delpt').onclick=()=>{
    const n=selDancer; const i=stretchPtIndexAt(n,curFrame); if(i<0) return;
    const before=stretchSnapshot(n); stretchPts[n].splice(i,1); const after=stretchSnapshot(n);
    recomposeDancer(n); pushCmd({type:'stretch', n, before, after});
    refreshDancerVisual(n); setFrame(curFrame); renderStretchPanel();
  };
  $('stretch-clearpts').onclick=()=>{
    const n=selDancer; if(!(stretchPts[n]&&stretchPts[n].length)) return;
    const before=stretchSnapshot(n); stretchPts[n]=[]; const after=stretchSnapshot(n);
    recomposeDancer(n); pushCmd({type:'stretch', n, before, after});
    refreshDancerVisual(n); setFrame(curFrame); renderStretchPanel();
  };

  $('refit-cur').onclick=()=>doRefit([curFrame]);
  $('refit-all').onclick=()=>doRefit(null);

  // overlay metriques : bouton "recalculer tout le clip"
  const mpc=$('mp-clip'); if(mpc) mpc.onclick=recomputeClipMetrics;
  // (« Définir comme départ » supprimé : le DEPART est toujours la métrique
  //  d'origine du clip, montrée automatiquement à l'ouverture.)

  $('sel-d').onchange=e=>{ selDancer=+e.target.value; updateSwatch(); attachGizmo(); updateJointFields(); syncGlobalFields(); renderStretchPanel(); };
  $('sel-j').onchange=e=>{ selJoint=+e.target.value; attachGizmo(); updateJointFields(); };
  ['x','y','z'].forEach(a=>{ $('j-'+a).onchange=applyJointFields; });
  $('reset-j').onclick=()=>{ const b=idx(selDancer,curFrame,selJoint);
    const before=[edited[b],edited[b+1],edited[b+2]];
    const after=[joints[b],joints[b+1],joints[b+2]];
    edited[b]=after[0];edited[b+1]=after[1];edited[b+2]=after[2];
    if(before[0]!==after[0]||before[1]!==after[1]||before[2]!==after[2])
      pushCmd({type:'joint', n:selDancer, t:curFrame, j:selJoint, before, after});
    setFrame(curFrame); };

  // sauvegarde = bundle .motion (session) ; pastille + bouton dédié.
  $('save-pill').onclick=saveBundle;
  $('export-pkl').onclick=exportPkl;

  // --- trois points d'entree de chargement (onglet Clip) ---
  if($('load-file'))    $('load-file').onclick=openPklPicker;
  if($('load-project')) $('load-project').onclick=openPicker;
  if($('load-folder'))  $('load-folder').onclick=openFolderDialog;
  // ancien bouton "Changer de clip" (ecran d'accueil / compat) -> liste des projets
  if($('change-clip'))  $('change-clip').onclick=openPicker;

  // --- liste unifiee des projets : nav, recherche, tri, rafraichissement ---
  if($('proj-search'))  $('proj-search').oninput=e=>{ PROJ_FILTER=e.target.value; renderProjectList(); };
  if($('proj-prev'))    $('proj-prev').onclick=()=>projStep(-1);
  if($('proj-next'))    $('proj-next').onclick=()=>projStep(1);
  if($('proj-refresh')) $('proj-refresh').onclick=()=>refreshProjects(true);
  if($('proj-metrics-recalc')) $('proj-metrics-recalc').onclick=recalcAllMetrics;

  // --- "Charger un fichier" : modale liste des .pkl ---
  if($('pkl-close'))  $('pkl-close').onclick=closePklPicker;
  if($('pkl-search')) $('pkl-search').oninput=e=>renderPklList(e.target.value);
  if($('pkl-modal'))  $('pkl-modal').addEventListener('click',e=>{ if(e.target.id==='pkl-modal') closePklPicker(); });

  // --- "Charger un dossier" : dialogue 3 dossiers (import de fond) ---
  if($('folder-go'))     $('folder-go').onclick=importFolder;
  if($('folder-cancel')) $('folder-cancel').onclick=closeFolderDialog;
  if($('folder-modal'))  $('folder-modal').addEventListener('click',e=>{ if(e.target.id==='folder-modal') closeFolderDialog(); });
  if($('fm-pkl-browse'))    $('fm-pkl-browse').onclick=()=>openBrowse('fm-pkl');
  if($('fm-videos-browse')) $('fm-videos-browse').onclick=()=>openBrowse('fm-videos');
  if($('fm-audio-browse'))  $('fm-audio-browse').onclick=()=>openBrowse('fm-audio');

  // --- panneau Source : pkl/videos/audio/smpl reglables depuis l'UI (zero CLI) ---
  if($('cfg-apply')){
    // (le pre-remplissage + has_metrics est fait par loadProjectConfig() au boot)
    $('cfg-apply').onclick=applyConfig;
    $('cfg-data-browse').onclick=()=>openBrowse('cfg-data');
    $('cfg-videos-browse').onclick=()=>openBrowse('cfg-videos');
    if($('cfg-audio-browse')) $('cfg-audio-browse').onclick=()=>openBrowse('cfg-audio');
    $('cfg-smpl-browse').onclick=()=>openBrowse('cfg-smpl');
    $('browse-close').onclick=closeBrowse;
    $('browse-choose').onclick=chooseBrowse;
    $('browse-modal').addEventListener('click',e=>{ if(e.target===$('browse-modal')) closeBrowse(); });
  }

  $('undo').onclick=undo;
  $('redo').onclick=redo;
  // #lang-sel a été retiré du DOM (langue gérée par #set-lang dans Paramètres).
  if($('lang-sel')) $('lang-sel').onchange=e=>applyLang(e.target.value);

  renderer.domElement.addEventListener('pointerdown',pick);
  window.addEventListener('keydown',e=>{
    // une modale est ouverte : ses propres raccourcis (Tab/Echap/Entree) priment ;
    // on n'execute aucun raccourci global (espace=lecture, fleches, gizmo, Ctrl+S…).
    if(_modalStack.length) return;
    const ctrl=e.ctrlKey||e.metaKey;
    // Ctrl+Maj+S : telecharge le .pkl corrige ; Ctrl+S : sauve sur le serveur.
    // (avant le filtre INPUT/SELECT pour marcher quel que soit le focus)
    if(ctrl && e.shiftKey && (e.key==='s'||e.key==='S')){ e.preventDefault(); exportPkl(); return; }
    if(ctrl && !e.shiftKey && (e.key==='s'||e.key==='S')){ e.preventDefault(); saveBundle(); return; }
    if(ctrl && (e.key==='z'||e.key==='Z')){
      if(e.shiftKey){ redo(); } else { undo(); } e.preventDefault(); return;
    }
    if(ctrl && (e.key==='y'||e.key==='Y')){ redo(); e.preventDefault(); return; }
    // Alt+◀ / Alt+▶ : projet precedent / suivant dans la liste triee courante.
    // (avant le filtre INPUT pour rester actif meme depuis le champ de recherche)
    if(e.altKey && e.key==='ArrowLeft'){ e.preventDefault(); projStep(-1); return; }
    if(e.altKey && e.key==='ArrowRight'){ e.preventDefault(); projStep(1); return; }
    // « ? » (Shift+/) : ouvre l'aide raccourcis. Avant le filtre INPUT/SELECT ?
    // Non : on ne veut pas l'intercepter quand on tape dans un champ.
    if(e.target.tagName==='INPUT'||e.target.tagName==='SELECT'||e.target.tagName==='TEXTAREA') return;
    if(e.key==='?'){ e.preventDefault(); openShortcuts(); return; }
    if(e.key==='w'||e.key==='g') tcontrols.setMode('translate');
    if(e.key==='r') tcontrols.setMode('rotate');
    if(e.key===' '){ e.preventDefault(); $('play').click(); }
    if(e.key==='ArrowRight'){ playing=false; syncMeshPrefetch(); setFrame(curFrame+1); }
    if(e.key==='ArrowLeft'){ playing=false; syncMeshPrefetch(); setFrame(curFrame-1); }
  });

  updateHUD();
  renderSavePill();
}

// accordeon exclusif : ouvrir l'un ferme l'autre ; pilote le gizmo
function onAccordion(e){
  if(_accLock) return;
  const other = (e.target.id==='acc-global') ? $('acc-joints') : $('acc-global');
  if(e.target.open){
    _accLock=true; other.open=false; _accLock=false;
  } else if(!other.open){
    // ne jamais tout fermer : reouvre celui qu'on vient de fermer
    _accLock=true; e.target.open=true; _accLock=false;
    return;
  }
  dancerMoveMode = $('acc-global').open;   // Global ouvert -> gizmo bassin
  localStorage.setItem('pe.editAccordion', dancerMoveMode?'global':'joints');
  attachGizmo();
}

function setView(which){
  const c=centroid(); const d=4.5;
  if(which==='front')  camera.position.set(c.x,    c.y-d,    c.z+0.4);
  if(which==='back')   camera.position.set(c.x,    c.y+d,    c.z+0.4);
  if(which==='left')   camera.position.set(c.x-d,  c.y,      c.z+0.4);
  if(which==='right')  camera.position.set(c.x+d,  c.y,      c.z+0.4);
  if(which==='top')    camera.position.set(c.x,    c.y-0.01, c.z+d);
  if(which==='bottom') camera.position.set(c.x,    c.y-0.01, c.z-d);
  orbit.target.copy(c); orbit.update();
}

// HUD raccourcis retire de l'UI a la demande de l'utilisatrice : no-op
// (conserve pour ne pas casser les appels existants applyLang/bindUI).
function updateHUD(){}

// ---- onglets ----
function bindTabs(){
  const btns=Array.from($('tabs').querySelectorAll('button'));
  btns.forEach((b,i)=>{
    b.onclick=()=>setTab(b.dataset.tab);
    // navigation clavier ARIA dans le tablist : fleches gauche/droite + Home/Fin.
    b.addEventListener('keydown',e=>{
      let j=null;
      if(e.key==='ArrowRight'||e.key==='ArrowDown') j=(i+1)%btns.length;
      else if(e.key==='ArrowLeft'||e.key==='ArrowUp') j=(i-1+btns.length)%btns.length;
      else if(e.key==='Home') j=0;
      else if(e.key==='End') j=btns.length-1;
      if(j!=null){ e.preventDefault(); setTab(btns[j].dataset.tab); btns[j].focus(); }
    });
  });
  // restaure accordeon
  const acc=localStorage.getItem('pe.editAccordion')||'global';
  _accLock=true;
  $('acc-global').open=(acc==='global'); $('acc-joints').open=(acc==='joints');
  _accLock=false;
  dancerMoveMode = $('acc-global').open;
  // onglet initial : celui sauvegarde, sinon Clip (sera force a Edit a l'ouverture d'un clip)
  setTab(localStorage.getItem('pe.tab') || 'clip');
}
function setTab(name){
  // garde-fou : un pe.tab perime ('display'/'export', onglets supprimes) -> repli sur Clip
  if(!TAB_NAMES.includes(name)) name='clip';
  $('tabs').querySelectorAll('button').forEach(b=>{
    const on=(b.dataset.tab===name);
    b.classList.toggle('on', on);
    // ARIA tablist : l'onglet actif est selectionne et seul focusable (roving tabindex).
    b.setAttribute('aria-selected', on?'true':'false');
    b.tabIndex = on?0:-1;
  });
  document.querySelectorAll('#tab-body .tab-content').forEach(c=>{ c.hidden = (c.dataset.tab!==name); });
  localStorage.setItem('pe.tab', name);
}

// ---- refit SMPL ----
let refitBusy=false;
async function doRefit(framesArg){
  if(refitBusy) return;
  refitBusy=true;
  const st=$('refit-status');
  const label = framesArg ? `${t('msg.frame')} ${framesArg[0]}` : `${T} ${t('msg.frames')}`;
  st.style.color='#e7c14b';
  st.textContent=tf('js.refit.run',{label});
  const body = { N, T, J, joints:Array.from(edited) };
  if(framesArg) body.frames=framesArg;
  if(CLIP_NAME) body.clip=CLIP_NAME;
  body.source=CLIP_SOURCE;
  // overlay « occupe » uniquement pour le refit complet (long) : le refit d'une
  // seule frame est rapide et ne doit pas voiler l'ecran.
  const _overlay = !framesArg;
  if(_overlay) showOverlay(t('busy.refit'));
  // boutons declencheurs grises pendant l'operation (evite double-clic).
  ['refit-cur','refit-all'].forEach(id=>{ const e=$(id); if(e) e.disabled=true; });
  try{
    const t0=performance.now();
    const r=await fetch('/refit',{method:'POST',
      headers:{'Content-Type':'application/json'}, body:JSON.stringify(body)});
    if(!r.ok){ throw new Error(await errMsg(r)); }
    const shape=(r.headers.get('X-Refit-Shape')||'').split(',').map(Number);
    const frames=(r.headers.get('X-Refit-Frames')||'').split(',').filter(s=>s!=='').map(Number);
    const err=(r.headers.get('X-Refit-Err')||'').split(',');
    const buf=await r.arrayBuffer();
    const verts=new Float32Array(buf);
    applyRefitVerts(verts, shape, frames);
    const dt=((performance.now()-t0)/1000).toFixed(1);
    st.style.color='#7fd18b';
    st.textContent=tf('js.refit.ok',{label, eb:err[0], ea:err[1], dt})+
      (meshObjs.length&&meshObjs[0].visible?'':t('js.refit.activate'));
  }catch(e){
    st.style.color='#ff7777';
    st.textContent=t('js.refit.fail')+e.message;
  }finally{ refitBusy=false; if(_overlay) hideOverlay();
    // ne reactive que si un clip est ouvert (sinon gateControls les garde grises).
    if(DATA){ ['refit-cur','refit-all'].forEach(id=>{ const e=$(id); if(e) e.disabled=false; }); }
  }
}

async function applyRefitVerts(verts, shape, frames){
  const [rN,rTsel,V] = shape;
  // si un maillage LIVE etait actif, on bascule sur le maillage refit (verts en
  // memoire) : on jette les meshes live + leur cache pour eviter tout melange.
  if(meshLive){
    for(const m of meshObjs){ scene.remove(m); m.geometry?.dispose?.(); m.material?.dispose?.(); }
    meshObjs=[]; meshLive=false; meshFaces=null; meshCache.clear();
    baseMeshCache.clear(); baseMeshInflight.clear();
    meshPrefetchOn=false; meshInflight.clear();
    meshFetchSeq++; if(meshDebounce){ clearTimeout(meshDebounce); meshDebounce=null; }
  }
  if(!meshObjs.length){
    if(!DATA.mesh){
      DATA.mesh={verts_shape:[N,T,V,3], verts_file:null, faces_file:'mesh_faces.bin'};
    }
    await loadMeshForRefit(V);
  }
  if(!DATA._verts){
    DATA._verts=new Float32Array(N*T*V*3); DATA._V=V;
  }
  const stride=V*3;
  for(let n=0;n<rN;n++){
    for(let ti=0;ti<rTsel;ti++){
      const t=frames[ti];
      const dst=((n*T+t)*V)*3;
      const src=((n*rTsel+ti)*V)*3;
      DATA._verts.set(verts.subarray(src,src+stride), dst);
    }
  }
  meshObjs.forEach(m=>m.visible=true); $('t-mesh').classList.add('on');
  setFrame(curFrame);
  reapplyBgRemove();   // un refit ne doit pas faire reapparaitre le fond video
}

async function loadMeshForRefit(V){
  // faces : via le backend (/mesh_faces, marche meme sans mesh_verts.bin sur
  // disque), sinon fichier statique pour le clip local (data/clip).
  let fb=null;
  if(CLIP_NAME){
    fb=await fetch(`/mesh_faces?clip=${encodeURIComponent(CLIP_NAME)}&source=${CLIP_SOURCE}`).then(r=>r.ok?r.arrayBuffer():null);
  }
  if(!fb && DATA.mesh && DATA.mesh.faces_file){
    fb=await fetch(`${CLIP}/${DATA.mesh.faces_file}`).then(r=>r.ok?r.arrayBuffer():null);
  }
  if(!fb){ throw new Error('faces du maillage introuvables (impossible d\'afficher le maillage refité)'); }
  const faces=new Int32Array(fb);
  DATA._V=V;
  for(let n=0;n<N;n++){
    const g=new THREE.BufferGeometry();
    g.setAttribute('position', new THREE.BufferAttribute(new Float32Array(V*3),3));
    g.setIndex(Array.from(faces)); g.computeVertexNormals();
    const mat=new THREE.MeshStandardMaterial({color:DCOL[n%DCOL.length],
      transparent:true, opacity:0.82, roughness:0.55, metalness:0.0, side:THREE.DoubleSide});
    const mesh=new THREE.Mesh(g,mat); mesh.visible=false;
    mesh.castShadow=true; mesh.receiveShadow=true;
    mesh.frustumCulled=false;   // idem : pas de culling (bounding sphere obsolete apres maj des verts)
    scene.add(mesh); meshObjs.push(mesh);
  }
}

// ====================================================================
//  Maillage SMPL "live" (rapide) + métriques sur le CLIP ENTIER (a la demande)
//  - SMPL "live" : apres chaque edition, on refit une petite fenetre de frames
//    autour de curFrame (POST /metrics?want_verts) -> le maillage des joints
//    EDITES se met a jour tout seul ~LIVE_DEBOUNCE_MS apres le geste. RAPIDE.
//    (On n'utilise ICI que les verts ; les metriques de fenetre ne sont PAS
//    affichees car elles ne portent que sur 5 frames -> pas comparables a la
//    reference qui couvre tout le clip.)
//  - Metriques : TOUJOURS calculees sur le CLIP ENTIER (comparable au dataset).
//    Lent (~15 s) -> declenche a la demande par le bouton « recalculer ».
//    Toute edition INVALIDE la colonne « actuel » (remise a —) tant qu'on n'a
//    pas recalcule, pour ne jamais comparer des portions differentes.
// ====================================================================
function metricsPlane(){
  // sol affiche (repere z-up des joints) : le plan ACTUEL si on edite le sol,
  // sinon celui du scene.json. None -> z=0 cote serveur.
  if(floorPlane) return [floorPlane[0],floorPlane[1],floorPlane[2]];
  if(DATA && DATA.floor) return DATA.floor;
  return null;
}

// fenetre de frames a refiter autour de curFrame (bornee [0,T-1]).
function liveFrames(){
  const a=Math.max(0,curFrame-LIVE_WINDOW), b=Math.min(T-1,curFrame+LIVE_WINDOW);
  const out=[]; for(let f=a;f<=b;f++) out.push(f); return out;
}

// ---- chemin "translation pure" (deplacement rigide) ----------------------
// Detecte si le danseur n a ete deplace par une TRANSLATION PURE : tous ses 24
// joints partagent le MEME delta (vs la base `joints`) a chaque frame. Renvoie
// {rigid, off:Float32Array(T*3)}. Si rigide, on peut afficher le maillage =
// verts de BASE (poses d'origine) + off, SANS refit (instantane, pieds intacts).
const RIGID_EPS=1e-4;   // m — meme tolerance que detect_rigid cote serveur
function dancerRigidOffset(n){
  const off=new Float32Array(T*3);
  let edits=false;
  for(let t=0;t<T;t++){
    // delta du joint 0 = candidat offset commun de la frame
    const b0=idx(n,t,0);
    const ox=edited[b0]-joints[b0], oy=edited[b0+1]-joints[b0+1], oz=edited[b0+2]-joints[b0+2];
    if(Math.abs(ox)>RIGID_EPS||Math.abs(oy)>RIGID_EPS||Math.abs(oz)>RIGID_EPS) edits=true;
    for(let j=1;j<J;j++){
      const b=idx(n,t,j);
      if(Math.abs((edited[b]-joints[b])-ox)>RIGID_EPS) return {rigid:false};
      if(Math.abs((edited[b+1]-joints[b+1])-oy)>RIGID_EPS) return {rigid:false};
      if(Math.abs((edited[b+2]-joints[b+2])-oz)>RIGID_EPS) return {rigid:false};
    }
    off[t*3]=ox; off[t*3+1]=oy; off[t*3+2]=oz;
  }
  return {rigid:true, off, edits};
}

// recupere les verts de BASE (poses d'origine, /mesh_frame) de la frame t.
// Cache LRU dedie (baseMeshCache) pour ne pas melanger avec les verts edites.
async function loadBaseMeshVerts(t){
  if(baseMeshCache.has(t)) return baseMeshCache.get(t);
  if(baseMeshInflight.has(t)) return null;
  baseMeshInflight.add(t);
  setLoadHud('ghost', true);   // HUD « Mouvement » : verts d'origine en cours de fetch
  try{
    const r=await fetch(`/mesh_frame?clip=${encodeURIComponent(CLIP_NAME)}&source=${CLIP_SOURCE}&frame=${t}&v=${MESH_VERSION}`);
    if(!r.ok) throw new Error(`/mesh_frame ${r.status}`);
    const v=decodeVerts(await r.arrayBuffer());
    baseMeshCache.set(t,v);
    while(baseMeshCache.size>MESH_CACHE_MAX){
      const oldest=baseMeshCache.keys().next().value; baseMeshCache.delete(oldest);
    }
    return v;
  }catch(e){ return null; }
  finally{ baseMeshInflight.delete(t); setLoadHud('ghost', baseMeshInflight.size>0); }
}

// ====================================================================
//  Fantome « avant » : maillage du motion D'ORIGINE (pre-edition) en
//  semi-transparent, superpose au maillage/squelette courant (= apres).
//  Verts = loadBaseMeshVerts(t) (cache /mesh_frame des poses chargees,
//  jamais affectees par les editions live ni par « Corriger le motion »).
// ====================================================================
const GHOST_COLOR=0xcfcfcf;   // gris neutre, distinct des couleurs danseurs

// charge les faces SMPL si besoin puis construit N meshes ghost (1x par clip).
async function buildGhostObjs(){
  if(ghostObjs.length) return true;
  if(!CLIP_NAME) return false;
  try{
    let faces=meshFaces;
    if(!faces){
      const r=await fetch(`/mesh_faces?clip=${encodeURIComponent(CLIP_NAME)}&source=${CLIP_SOURCE}`);
      if(!r.ok) throw new Error(`/mesh_faces ${r.status}`);
      faces=new Int32Array(await r.arrayBuffer());
      if(!meshFaces) meshFaces=faces;   // partage si le maillage live n'a pas encore charge
    }
    const faceArr=Array.from(faces);
    for(let n=0;n<N;n++){
      const g=new THREE.BufferGeometry();
      g.setAttribute('position', new THREE.BufferAttribute(new Float32Array(MESH_V*3),3));
      g.setIndex(faceArr);
      g.computeVertexNormals();
      const mat=new THREE.MeshStandardMaterial({color:GHOST_COLOR,
        transparent:true, opacity:0.25, depthWrite:false,
        roughness:0.9, metalness:0.0, side:THREE.DoubleSide});
      const mesh=new THREE.Mesh(g, mat); mesh.visible=true;
      mesh.castShadow=false; mesh.receiveShadow=false;
      mesh.frustumCulled=false;   // verts maj a la volee : bounding sphere obsolete
      mesh.renderOrder=2;         // dessine apres le maillage solide (tri transparence)
      scene.add(mesh); ghostObjs.push(mesh);
    }
    return true;
  }catch(e){
    setMeshStatus('✗ '+e.message, '#ff7777');
    return false;
  }
}

// detruit proprement les meshes ghost (toggle OFF ou changement de clip).
function disposeGhost(){
  for(const m of ghostObjs){ scene.remove(m); m.geometry?.dispose?.(); m.material?.dispose?.(); }
  ghostObjs=[];
}

// applique au ghost les verts d'ORIGINE de la frame t (pre-edition). Anti-course
// via ghostFrameSeq : un scrub rapide ne laisse pas une vieille frame s'afficher.
async function updateGhostFrame(t){
  if(!ghostOn || !ghostObjs.length) return;
  const seq=++ghostFrameSeq;
  const base=await loadBaseMeshVerts(t);
  if(!base || seq!==ghostFrameSeq || !ghostOn || curFrame!==t) return;
  const stride=MESH_V*3;
  for(let n=0;n<N && n<ghostObjs.length;n++){
    const pos=ghostObjs[n].geometry.attributes.position.array;
    pos.set(base.subarray(n*stride, (n+1)*stride));
    ghostObjs[n].geometry.attributes.position.needsUpdate=true;
    ghostObjs[n].geometry.computeVertexNormals();
  }
}

// bascule du toggle « Fantome avant ».
async function toggleGhost(){
  if(!N){ return; }
  ghostOn=!ghostOn;
  $('t-ghost').classList.toggle('on', ghostOn);
  if(ghostOn){
    const ok=await buildGhostObjs();
    if(!ok){ ghostOn=false; $('t-ghost').classList.remove('on'); return; }
    ghostObjs.forEach(m=>m.visible=true);
    await updateGhostFrame(curFrame);
  }else{
    disposeGhost();
  }
}

// applique au maillage de la frame t, pour les danseurs rigides, leurs verts de
// base + offset (instantane). `rigids` = {n -> off Float32Array(T*3)}. Renvoie
// true si tous les danseurs voulus ont pu etre affiches (base verts dispo).
async function applyRigidLiveFrame(t, rigids){
  if(!meshObjs.length) return false;
  const base=await loadBaseMeshVerts(t);
  if(!base) return false;
  if(t!==curFrame || !meshVisible()) return true;   // frame a change : abandon propre
  const stride=MESH_V*3;
  for(const n in rigids){
    const off=rigids[n]; const ox=off[t*3],oy=off[t*3+1],oz=off[t*3+2];
    const src=(+n)*stride;
    const pos=meshObjs[+n].geometry.attributes.position.array;
    for(let k=0;k<MESH_V;k++){
      pos[k*3]  =base[src+k*3]  +ox;
      pos[k*3+1]=base[src+k*3+1]+oy;
      pos[k*3+2]=base[src+k*3+2]+oz;
    }
    meshObjs[+n].geometry.attributes.position.needsUpdate=true;
    meshObjs[+n].geometry.computeVertexNormals();
  }
  refreshFloorDist();
  return true;
}

// refit live de la fenetre courante : met a jour le MAILLAGE uniquement
// (les metriques de fenetre ne sont pas affichees — voir l'entete du bloc).
async function liveRefitMesh(){
  if(!CLIP_NAME || !DATA){ return; }
  // classe les danseurs : rigides (translation pure) vs par-joint. Les rigides
  // s'affichent INSTANTANEMENT (base + offset, pieds intacts), sans refit. On
  // n'envoie au serveur que s'il reste au moins un danseur edite par-joint.
  const rigids={};            // n -> offset (T*3) pour les danseurs rigides
  let anyNonRigid=false;
  for(let n=0;n<N;n++){
    const r=dancerRigidOffset(n);
    if(r.rigid){ if(r.edits) rigids[n]=r.off; }   // inchange -> rien a faire
    else anyNonRigid=true;
  }
  // affichage rigide immediat de la frame courante (et de la fenetre, pour le scrub).
  if(Object.keys(rigids).length){
    applyRigidLiveFrame(curFrame, rigids);
  }
  if(!anyNonRigid){ return; }   // tout est rigide -> pas de refit serveur

  if(liveBusy){ liveDirty=true; return; }   // un refit tourne -> on relancera
  liveBusy=true; liveDirty=false;
  const frames=liveFrames();
  try{
    const body={ N, T, J, joints:Array.from(edited), clip:CLIP_NAME,
      source:CLIP_SOURCE, frames, iters:LIVE_ITERS, fps:fpsVal(),
      plane:metricsPlane(), heavy:false, want_verts:true };
    const r=await fetch('/metrics',{method:'POST',
      headers:{'Content-Type':'application/json'}, body:JSON.stringify(body)});
    if(!r.ok) throw new Error(await errMsg(r));
    const shape=(r.headers.get('X-Refit-Shape')||'').split(',').map(Number);
    const rframes=(r.headers.get('X-Refit-Frames')||'').split(',').filter(s=>s!=='').map(Number);
    const verts=new Float32Array(await r.arrayBuffer());
    applyLiveRefitFrame(verts, shape, rframes);   // maillage des joints edites
  }catch(e){
    // echec maillage live : silencieux (le squelette reste juste)
  }finally{
    liveBusy=false;
    if(liveDirty){ liveDirty=false; scheduleLive(); }   // edition survenue pendant -> rejoue
  }
}

// applique les verts refites (joints EDITES) au maillage affiche, frame par
// frame de la fenetre. Ne casse pas la machinerie live : on remplit le cache
// avec ces verts edites (ainsi scrub dans la fenetre montre l'edition) et on
// affiche la frame courante. shape=[N,Tsel,V,3], rframes=indices absolus.
function applyLiveRefitFrame(verts, shape, rframes){
  if(!meshObjs.length) return;
  const [rN,rTsel,V]=shape; const stride=V*3;
  for(let ti=0;ti<rTsel;ti++){
    const t=rframes[ti];
    // recompose la frame complete (N,V,3) pour le cache + l'affichage.
    const full=new Float32Array(N*stride);
    for(let n=0;n<rN && n<N;n++){
      const src=((n*rTsel+ti)*V)*3;
      full.set(verts.subarray(src,src+stride), n*stride);
    }
    if(meshLive) cacheMeshFrame(t, full);   // scrub dans la fenetre = edition
    if(t===curFrame) applyMeshVerts(full);  // affiche tout de suite
  }
}

// appelee a chaque edition : 1) rafraichit le maillage live (rapide),
// 2) INVALIDE la colonne « actuel » des metriques (clip entier) -> il faudra
//    recalculer pour la remplir (sinon on comparerait des choses differentes).
function scheduleLive(){
  invalidateClipMetrics();
  if(!meshShouldBeLive()) return;        // maillage masque -> pas de refit live
  // translation pure (tous les danseurs edites rigides) : pas d'auto-refit ni de
  // debounce — on applique base + offset EN DIRECT (instantane, pieds intacts).
  let anyNonRigid=false, anyRigid=false;
  for(let n=0;n<N;n++){
    const r=dancerRigidOffset(n);
    if(r.rigid){ if(r.edits) anyRigid=true; } else anyNonRigid=true;
  }
  if(!anyNonRigid){
    if(liveTimer){ clearTimeout(liveTimer); liveTimer=null; }
    if(anyRigid) liveRefitMesh();         // applique l'offset rigide tout de suite
    return;
  }
  // au moins une edition par-joint -> chemin refit (avec debounce). liveRefitMesh
  // affiche aussi les danseurs rigides instantanement en debut d'appel.
  if(liveTimer) clearTimeout(liveTimer);
  liveTimer=setTimeout(()=>{ liveTimer=null; liveRefitMesh(); }, LIVE_DEBOUNCE_MS);
}

// le maillage doit-il refleter les editions en direct ? (toggle Maillage ON)
function meshShouldBeLive(){ return meshObjs.length>0 && meshObjs[0].visible; }

// une edition est survenue : la metrique « actuel » (clip entier) n'est plus a
// jour -> on la vide et on invite a recalculer.
function invalidateClipMetrics(){
  if(!metricsPanelOn) return;
  metricsCur=null; metricsDirty=true; renderMetricsPanel();
  setMetricsStatus(t('metrics.stale'), '#e7c14b');
}

// ---- métriques sur le CLIP ENTIER (bouton « recalculer ») : comparable au
//      dataset. Lent (~15 s). Remplit la colonne « actuel ». ----
// pristine = les joints affiches sont EXACTEMENT ceux d'origine (aucune edition nette).
function metricsArePristine(){
  if(!edited || !joints || edited.length!==joints.length) return false;
  for(let i=0;i<edited.length;i++){ if(Math.abs(edited[i]-joints[i])>1e-6) return false; }
  return true;
}
async function recomputeClipMetrics(){
  if(!CLIP_NAME || metricsClipBusy) return;
  // SANS edition : la metrique EXACTE = la reference pre-calculee (= pipeline
  // hors-outil, verifie a 0.000%). On n'applique PAS le refit (qui est lossy et
  // ajoutait l'ecart trompeur). Resultat : actuel == depart, ecart exactement nul.
  if(metricsArePristine() && metricsRef){
    metricsCur = Object.assign({}, metricsRef);
    metricsDirty=false; renderMetricsPanel();
    setMetricsStatus(t('metrics.pristine'), '#7fd18b');
    return;
  }
  metricsClipBusy=true;
  const btn=$('mp-clip'); if(btn) btn.disabled=true;
  setMetricsStatus(t('metrics.computing'), '#e7c14b');
  try{
    const body={ N, T, J, joints:Array.from(edited), clip:CLIP_NAME,
      source:CLIP_SOURCE, frames:null, iters:LIVE_ITERS, fps:fpsVal(),
      plane:metricsPlane(), heavy:true, want_verts:false };
    const r=await fetch('/metrics',{method:'POST',
      headers:{'Content-Type':'application/json'}, body:JSON.stringify(body)});
    if(!r.ok) throw new Error(await errMsg(r));
    const j=await r.json();
    metricsCur=j.metrics; metricsDirty=false; renderMetricsPanel();
    setMetricsStatus('✓ '+t('metrics.clipdone')+` (${j.time_s||''}s)`, '#7fd18b');
  }catch(e){
    setMetricsStatus('✗ '+e.message, '#ff8a8a');
  }finally{
    metricsClipBusy=false; const b=$('mp-clip'); if(b) b.disabled=false;
  }
}

function setMetricsStatus(msg,col){ const s=$('mp-status'); if(s){ s.textContent=msg; s.style.color=col||'#9aa0ac'; } }

// references = metriques pre-calculees du clip (picker). null si absentes.
function setMetricsRef(ref){
  metricsRef = (ref && Object.keys(ref).length) ? ref : null;
  metricsCur = null;
  renderMetricsPanel();
}

function fmtMetric(v, key){
  if(v==null || !isFinite(v)) return '—';
  const d=METRIC_DECIMALS[key]!=null?METRIC_DECIMALS[key]:2;
  return v.toFixed(d);
}

// construit/rafraichit le tableau de l'overlay (reference -> actuel, colore).
function renderMetricsPanel(){
  const rows=$('mp-rows'); if(!rows) return;
  let html='';
  // cles connues (ordre METRIC_ORDER) puis toute cle supplementaire renvoyee
  // par le plugin. Le libelle est traduit si connu, sinon humanise (cle brute).
  for(const key of metricKeysToRender()){
    const ref = metricsRef ? metricsRef[key] : null;
    const cur = metricsCur ? metricsCur[key] : null;
    let cls='mp-same', arrow='·';
    if(ref!=null && cur!=null && isFinite(ref) && isFinite(cur)){
      const eps=Math.max(1e-9, Math.abs(ref)*0.005);   // ~0.5% = "egal"
      if(cur < ref-eps){ cls='mp-better'; arrow='↓'; }       // plus bas = mieux
      else if(cur > ref+eps){ cls='mp-worse'; arrow='↑'; }
    }
    html+=`<tr><td class="mp-name">${escHtml(metricLabel(key))}</td>`+
      `<td class="mp-ref">${fmtMetric(ref,key)}</td>`+
      `<td class="mp-arrow">${arrow}</td>`+
      `<td class="mp-cur ${cls}">${fmtMetric(cur,key)}</td></tr>`;
  }
  rows.innerHTML=html;
}

function showMetricsPanel(on){
  metricsPanelOn=!!on;
  $('metrics-panel').classList.toggle('show', metricsPanelOn);
  // garde l'item de menu « Métriques » (Affichage) en phase avec l'état réel.
  const it=$('t-metrics');
  if(it){ it.classList.toggle('on', metricsPanelOn); it.setAttribute('aria-checked', metricsPanelOn?'true':'false'); }
}

// ---- cartouche « Sauvegarder » (en haut) : etat dirty/saved/busy ----
// (saveDirty/saveBusy/exportBusy sont declares en haut du module : evite la TDZ)
function markDirty(){ if(!saveDirty){ saveDirty=true; renderSavePill(); }
  if(typeof scheduleAutosave==='function') scheduleAutosave(); }
function markSaved(){ saveDirty=false; saveDoneThisSession=true; renderSavePill();
  if(typeof clearDraft==='function') clearDraft(); }
// reflete l'etat courant sur la pastille (texte + classe + libelle i18n).
function renderSavePill(){
  const p=$('save-pill'), txt=$('save-pill-txt'); if(!p||!txt) return;
  p.classList.remove('saved','busy');
  // pas de clip ouvert : pastille neutre/desactivee (jamais « Enregistré » a vide)
  if(!DATA || !CLIP_NAME){
    p.disabled=true; txt.textContent=t('save.dirty'); return;
  }
  p.disabled=false;
  if(saveBusy){ p.classList.add('busy'); txt.textContent=t('save.saving'); return; }
  if(saveDirty){ txt.textContent=t('save.dirty'); return; }
  // non modifie : « Enregistré » uniquement apres une vraie sauvegarde de cette
  // session ; sinon on reste sur le libelle neutre (« Enregistrer »).
  if(saveDoneThisSession){ p.classList.add('saved'); txt.textContent=t('save.saved'); }
  else { txt.textContent=t('save.dirty'); }
}

async function savePkl(){
  if(saveBusy || !DATA) return;
  if(!CLIP_NAME){
    $('save-status').style.color='#ff7777';
    $('save-status').textContent=t('js.save.example');
    return;
  }
  saveBusy=true; renderSavePill();
  const st=$('save-status');
  st.style.color='#e7c14b';
  st.textContent=t('js.save.run');
  try{
    const body={ N, T, J, joints:Array.from(edited), source:CLIP_SOURCE };
    const r=await fetch(`/save_pkl?clip=${encodeURIComponent(CLIP_NAME)}`,{method:'POST',
      headers:{'Content-Type':'application/json'}, body:JSON.stringify(body)});
    if(!r.ok) throw new Error(await errMsg(r));
    const j=await r.json();
    st.style.color='#7fd18b';
    st.innerHTML=t('js.save.ok')+`<code>${j.path}</code><br>${t('js.save.poses')} ${j.shape_poses.join('×')}, `+
      `${t('js.save.trans')} ${j.shape_trans.join('×')} — ${t('js.save.jointerr')} ${j.err_before}→${j.err_after} m (${j.time_s}s). `+
      t('js.save.untouched');
    saveBusy=false; markSaved();
  }catch(e){
    st.style.color='#ff7777';
    st.textContent=t('js.save.fail')+e.message;
    saveBusy=false; renderSavePill();
  }
}

// ---- Export (.pkl) : telecharge le pkl corrige sur la machine de l'utilisatrice ----
// POST /export_pkl -> octets pkl (Content-Disposition attachment) -> <a download>.
async function exportPkl(){
  if(exportBusy) return;
  const btn=$('export-pkl');
  if(!DATA || !CLIP_NAME){
    toast(t('gate.noclip'), 'err');
    return;
  }
  exportBusy=true; if(btn){ btn.disabled=true; btn.textContent=t('export.preparing'); }
  try{
    const body={ N, T, J, joints:Array.from(edited), source:CLIP_SOURCE };
    const r=await fetch(`/export_pkl?clip=${encodeURIComponent(CLIP_NAME)}&source=${encodeURIComponent(CLIP_SOURCE)}`,
      {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify(body)});
    if(!r.ok) throw new Error(await errMsg(r));
    // nom de fichier : Content-Disposition si fourni, sinon <clip>_corrige.pkl
    let fname=(CLIP_NAME||'clip')+'_corrige.pkl';
    const cd=r.headers.get('Content-Disposition')||'';
    const m=cd.match(/filename="?([^"]+)"?/);
    if(m) fname=m[1];
    const blob=await r.blob();
    const a=document.createElement('a'); a.href=URL.createObjectURL(blob);
    a.download=fname; document.body.appendChild(a); a.click(); a.remove();
    setTimeout(()=>URL.revokeObjectURL(a.href), 4000);
    if(btn) btn.textContent=t('export.done');
    setTimeout(()=>{ if(btn) btn.textContent=t('export.pkl'); }, 1800);
  }catch(e){
    $('save-status').style.color='#ff7777';
    $('save-status').textContent=t('export.fail')+e.message;
    toast(t('export.fail')+e.message, 'err');
    if(btn) btn.textContent=t('export.pkl');
  }finally{ exportBusy=false; if(btn) btn.disabled=false; }
}

// ====================================================================
//  Workspace / bundles .motion (nouveau) — session save/load + dossiers
// --------------------------------------------------------------------
//  Un bundle .motion encapsule UNE session : l'original (intact) + les
//  joints EDITES + le placement de la vidéo (billboard) + commentaires +
//  un instantané des métriques. C'est la sauvegarde « de travail » : elle
//  N'écrit PAS de .pkl (ça reste le rôle d'« Exporter (.pkl) »).
// ====================================================================

// place vidéo (billboard) : lit l'état courant des champs de l'onglet Vidéo
// + l'offset temporel du fond -> objet sérialisable pour le bundle.
function getVideoParams(){
  const num=(id,def)=>{ const v=parseFloat($(id) && $(id).value); return isFinite(v)?v:def; };
  return {
    pos_x:   num('bg-x', 0),
    pos_y:   num('bg-y', 0.25),
    pos_z:   num('bg-z', 0.05),
    scale:   num('bg-s', 0.5),
    opacity: num('bg-o', 1.0),
    visible: $('bg-on') ? !!$('bg-on').checked : true,
    bg_offset: (DATA && DATA.bg_offset!=null) ? DATA.bg_offset : 0,
  };
}

// restaure le placement vidéo depuis un bundle : remet les champs ET applique
// au billboard 3D (mêmes effets que les handlers oninput de l'onglet Vidéo).
function applyVideoParams(vp){
  if(!vp) return;
  const set=(id,v)=>{ if($(id)!=null && v!=null) $(id).value=v; };
  if(vp.pos_x!=null)   set('bg-x', (+vp.pos_x).toFixed(3));
  if(vp.pos_y!=null)   set('bg-y', (+vp.pos_y).toFixed(3));
  if(vp.pos_z!=null)   set('bg-z', (+vp.pos_z).toFixed(3));
  if(vp.scale!=null)   set('bg-s', (+vp.scale).toFixed(3));
  if(vp.opacity!=null) set('bg-o', (+vp.opacity).toFixed(2));
  if(vp.visible!=null && $('bg-on')) $('bg-on').checked=!!vp.visible;
  // applique au mesh du fond (si déjà construit) : position/échelle/visibilité.
  if(bg){
    if(vp.pos_x!=null) bg.position.x=+vp.pos_x;
    if(vp.pos_y!=null) bg.position.y=+vp.pos_y;
    if(vp.pos_z!=null) bg.position.z=+vp.pos_z;
    if(vp.scale!=null){ const s=+vp.scale; bg.scale.set(s,s,s); }
    if(vp.visible!=null) bg.visible=!!vp.visible;
    if(vp.opacity!=null && bg.material) bg.material.opacity=+vp.opacity;
  }
}

// ---- Enregistrer (.motion) : sauve la SESSION (POST /bundle/save). ----
// Remplace l'ancien savePkl(/save_pkl) : même UX (pastille sauvegardé/dirty,
// Ctrl+S) mais écrit un bundle .motion, sans toucher au .pkl.
async function saveBundle(){
  if(saveBusy) return;
  if(!DATA || !CLIP_NAME){
    toast(t('gate.noclip'), 'err');
    return;
  }
  saveBusy=true; renderSavePill();
  const st=$('save-status');
  st.style.display='block';
  st.style.color='#e7c14b';
  st.textContent=t('bundle.save.run');
  try{
    const body={
      N, T, J,
      joints_edited: Array.from(edited),
      video_params:  getVideoParams(),
      comments:      commentsList,
      metrics:       metricsCur || metricsRef || null,
      source_clip:   CLIP_SOURCE,
    };
    const r=await fetch(`/bundle/save?name=${encodeURIComponent(CLIP_NAME)}`,{method:'POST',
      headers:{'Content-Type':'application/json'}, body:JSON.stringify(body)});
    if(!r.ok) throw new Error(await errMsg(r));
    const j=await r.json();
    st.style.color='#7fd18b';
    st.innerHTML=t('bundle.save.ok')+`<code>${j.path||CLIP_NAME+'.motion'}</code>`;
    saveBusy=false; markSaved();
    // la liste workspace a changé -> invalide le cache + rafraichit la table.
    WORKSPACE=null;
    refreshProjects(true);
  }catch(e){
    st.style.color='#ff7777';
    st.textContent=t('bundle.save.fail')+e.message;
    toast(t('bundle.save.fail')+e.message, 'err');
    saveBusy=false; renderSavePill();
  }
}

// ---- charge un bundle .motion (GET /bundle/load) comme un clip. ----
// Le bundle renvoie la même forme de scène que /load, PLUS {edited,
// video_params, comments, metrics} pour restaurer la session de travail.
async function loadBundleByName(name){
  showOverlay(tf('js.load.overlay',{name}));
  try{
    const r=await fetch(`/bundle/load?name=${encodeURIComponent(name)}`);
    if(!r.ok) throw new Error("/bundle/load — "+await errMsg(r));
    const data=await r.json();
    CLIP = data._clip_dir || `data/${name}`;
    CLIP_NAME = name;
    CLIP_SOURCE = data.source || 'original';
    MESH_VERSION = data.mesh_version || 0;   // cache-buster /mesh_frame (immutable)
    PROJ_CURRENT = name;            // surlignage + nav ◀ ▶ dans la liste des projets
    teardownScene();
    DATA = data;
    buildFromData();
    // restaure les joints édités si le bundle en fournit (sinon buildFromData
    // a déjà initialisé `edited` à partir des joints d'origine).
    if(data.edited && edited && data.edited.length===edited.length){
      edited.set(data.edited);
    }
    $('status').style.color='#7fd18b';
    $('status').textContent = `✓ ${DATA.name} — ${N} ${t('msg.dancers')}, ${T} ${t('msg.frames')} · .motion`;
    updateClipInfo();
    setTab('edit');
    pushRecent(CLIP_NAME, 'bundle', CLIP_SOURCE);   // fichiers récents (écran d'accueil)
    _skipDraftRestore=true;   // le bundle porte déjà ses édits : pas de restauration de brouillon
    await afterClipLoaded();
    // restaure le placement vidéo + les commentaires depuis le bundle.
    applyVideoParams(data.video_params);
    if(Array.isArray(data.comments)){ commentsList=data.comments; renderComments(); }
    // metriques de la session enregistree : DEPART (ref) deja posee par
    // afterClipLoaded() via sceneRefMetrics(). ACTUEL (cur) si le bundle l'a figee.
    if(data.metrics && typeof data.metrics==='object'){
      const cur=(data.metrics.cur && typeof data.metrics.cur==='object')
        ? data.metrics.cur
        : ((data.metrics.ref||data.metrics.cur)?null:data.metrics); // forme plate
      if(cur && Object.keys(cur).length){ metricsCur=cur; renderMetricsPanel(); }
    }
    setFrame(curFrame);          // ré-applique les édits restaurés à la frame courante
    markSaved();                 // fraîchement chargé depuis le .motion -> « sauvegardé »
    await warmFirstFrame();      // surcouche maintenue jusqu'à la 1re frame prête
  }catch(err){
    $('status').textContent = '✗ ' + err.message; $('status').style.color = '#ff7777';
  }finally{ hideOverlay(); }
}

// ---- Charger un dossier : import BATCH en tache de fond (3 dossiers optionnels). ----
// POST /import_folder {pkl_dir?, videos_dir?, audio_dir?} -> demarre un job. Des
// que le serveur a accepte, on FERME la modale et on suit l'avancee dans une
// ligne de statut persistante du panneau Projets (#proj-import-job). La liste se
// rafraichit a la fin. La modale ne reste jamais ouverte a attendre.
async function importFolder(){
  const st=$('folder-status');
  const body={};
  const pkl=($('fm-pkl').value||'').trim();
  const vid=($('fm-videos').value||'').trim();
  const aud=($('fm-audio').value||'').trim();
  if(pkl) body.pkl_dir=pkl;          // champs optionnels : omis = dossier configuré par défaut
  if(vid) body.videos_dir=vid;
  if(aud) body.audio_dir=aud;
  if(st){ st.style.color='#e7c14b'; st.textContent=t('folder.run'); }
  const btn=$('folder-go'); if(btn) btn.disabled=true;
  try{
    const r=await fetch('/import_folder',{method:'POST',
      headers:{'Content-Type':'application/json'}, body:JSON.stringify(body)});
    if(!r.ok) throw new Error(await errMsg(r));
    await r.json();
    // import demarre cote serveur : ferme la modale TOUT DE SUITE.
    if(btn) btn.disabled=false;
    closeFolderDialog();
    setImportJob(t('folder.run'), true);
    if(typeof toast==='function') toast(t('folder.run'), 'info');
    pollImportStatus();              // suit l'avancee (ligne persistante) + rafraichit a la fin
  }catch(e){
    if(st){ st.style.color='#ff7777'; st.textContent=t('folder.fail')+e.message; }
    toast(t('folder.fail')+e.message, 'err');
    if(btn) btn.disabled=false;
  }
}

// ligne de statut persistante de l'import (panneau Projets). show=false la cache.
function setImportJob(msg, show){
  const box=$('proj-import-job'), txt=$('proj-import-txt');
  if(txt) txt.textContent=msg||'';
  if(box) box.style.display=(show!==false && msg)?'block':'none';
}

// ---- polling GET /import_status : avancee de l'import de fond. ----
// {running, total, done, failed, current, imported_names}. A la fin : rafraichit
// la liste des projets et masque la ligne de statut.
function pollImportStatus(){
  if(_importPollTimer) clearTimeout(_importPollTimer);
  const tick=async()=>{
    let j=null;
    try{ const r=await fetch('/import_status'); if(r.ok) j=await r.json(); }catch(_){}
    if(!j){ _importPollTimer=setTimeout(tick,1500); return; }
    const total=j.total||0, done=j.done||0;
    const line=tf('folder.progress',{
      done, total,
      failed: j.failed? ' · '+j.failed+' échec'+(j.failed>1?'s':'') : '',
      current: j.current? ' · '+j.current : '',
    });
    setImportJob(line, true);
    if(j.running){ _importPollTimer=setTimeout(tick,1200); return; }
    // termine : rafraichit la liste des projets puis annonce + masque la ligne.
    await loadWorkspace(true); renderProjectList();
    const n=(j.imported_names?j.imported_names.length:done);
    if(typeof toast==='function') toast(t('folder.ok')+n, 'info');
    setImportJob('', false);
  };
  tick();
}

// ---- liste workspace (GET /workspace) : bundles .motion enregistrés. ----
// Mise en cache dans WORKSPACE (comme CLIPS). `force` recharge même si en cache.
async function loadWorkspace(force){
  if(WORKSPACE && !force) return WORKSPACE;
  try{
    const r=await fetch('/workspace');
    if(!r.ok) throw new Error('/workspace '+r.status);
    const j=await r.json();
    WORKSPACE=Array.isArray(j.bundles)?j.bundles:[];
  }catch(e){
    WORKSPACE=[];
  }
  return WORKSPACE;
}

// ====================================================================
//  Liste unifiee des projets (.motion) + 3 points d'entree de chargement
//  + job metriques de fond. Tout est dans l'onglet « Clip ».
// ====================================================================

// renvoie l'objet de metriques « reference » d'un bundle, robuste a la forme :
//   {ref:{...}, cur:{...}}  -> .ref
//   {metricName:value, ...} -> tel quel (forme plate)
function _bundleMetrics(b){
  const m=b && b.metrics;
  if(!m || typeof m!=='object') return null;
  if(m.ref && typeof m.ref==='object') return m.ref;
  if(m.cur && typeof m.cur==='object') return m.cur;
  return m;   // forme plate
}

// colonnes metriques de la table des projets. Si has_metrics est vrai, on
// AFFICHE TOUJOURS les colonnes (triables), même si certaines valeurs sont
// encore en cours de calcul (job de fond) -> placeholder « … ». L'ordre suit
// METRIC_ORDER (colonnes connues d'abord), puis toute clé supplémentaire.
function _metricColumns(){
  if(!PROJ_HAS_METRICS) return [];
  const set=new Set();
  for(const b of (WORKSPACE||[])){
    const m=_bundleMetrics(b);
    if(m) for(const k of Object.keys(m)) set.add(k);
  }
  // aucune valeur encore chargée : on retombe sur la liste canonique pour que
  // les colonnes apparaissent et soient triables dès le départ.
  if(!set.size) METRIC_ORDER.forEach(k=>set.add(k));
  // ordre stable : METRIC_ORDER d'abord, puis les clés inconnues en fin.
  const ordered=METRIC_ORDER.filter(k=>set.has(k));
  for(const k of set){ if(!ordered.includes(k)) ordered.push(k); }
  return ordered;
}

// libelle d'une colonne metrique : reutilise les libelles de tri connus (sort.*),
// sinon le nom brut.
function _metricLabel(k){
  const lbl=t('sort.'+k);
  return (lbl && lbl!=='sort.'+k) ? lbl : k;
}

// valeur triable d'un bundle pour la cle donnee (champ standard ou metrique).
function _projValue(b, key){
  switch(key){
    case 'name':        return (b.name||'').toLowerCase();
    case 'source_clip': return (b.source_clip||'').toLowerCase();
    case 'has_video':   return b.has_video?1:0;
    case 'has_music':   return b.has_music?1:0;
    case 'mtime':       return b.mtime||0;
    default: {           // metrique : null -> relegue en fin de tri
      const m=_bundleMetrics(b);
      const v=m && m[key];
      return (v==null||isNaN(v))? null : +v;
    }
  }
}

// applique filtre + tri courant et memorise l'ordre (_projOrder) pour la nav ◀ ▶.
function _projSorted(){
  const f=PROJ_FILTER.trim().toLowerCase();
  let list=(WORKSPACE||[]).slice();
  if(f) list=list.filter(b=>
    (b.name||'').toLowerCase().includes(f) ||
    (b.source_clip||'').toLowerCase().includes(f));
  // filtre par tags (ANY) : un clip passe s'il porte au moins un tag actif.
  if(PROJ_TAG_FILTER.size) list=list.filter(b=>
    clipTags(b.name).some(tg=>PROJ_TAG_FILTER.has(tg)));
  const key=PROJ_SORT_KEY, dir=PROJ_SORT_DIR;
  list.sort((a,b)=>{
    const va=_projValue(a,key), vb=_projValue(b,key);
    if(va==null&&vb==null) return 0;
    if(va==null) return 1;          // valeur manquante toujours en fin
    if(vb==null) return -1;
    if(va<vb) return -dir;
    if(va>vb) return  dir;
    return 0;
  });
  _projOrder=list.map(b=>b.name);
  return list;
}

// rendu de la table des projets (en-tetes cliquables + lignes + spinner metriques).
function renderProjectList(){
  const head=$('proj-head'), body=$('proj-body'), cnt=$('proj-count');
  if(!head||!body) return;
  const metricCols=_metricColumns();
  // ---- en-tetes : colonnes fixes + une par metrique ----
  const cols=[
    {key:'name',        label:t('col.name')},
    {key:'source_clip', label:t('col.source')},
    {key:'has_video',   label:t('col.video')},
    {key:'has_music',   label:t('col.music')},
    {key:'mtime',       label:t('col.mtime')},
    {key:'tags',        label:t('col.tags'), nosort:true},  // chips editables, non triable
    ...metricCols.map(k=>({key:k, label:_metricLabel(k), metric:true})),
  ];
  head.innerHTML='';
  for(const c of cols){
    const th=document.createElement('th');
    if(c.nosort){                       // colonne interactive : pas de tri
      th.textContent=c.label;
      th.className='proj-th tags';
      head.appendChild(th);
      continue;
    }
    const arrow=(PROJ_SORT_KEY===c.key)?(PROJ_SORT_DIR>0?' ▲':' ▼'):'';
    th.textContent=c.label+arrow;
    th.className='proj-th'+(c.metric?' metric':'')+(PROJ_SORT_KEY===c.key?' active':'');
    th.setAttribute('role','button'); th.tabIndex=0;
    const doSort=()=>{
      if(PROJ_SORT_KEY===c.key) PROJ_SORT_DIR=-PROJ_SORT_DIR;
      else { PROJ_SORT_KEY=c.key; PROJ_SORT_DIR=(c.key==='name'||c.key==='source_clip')?1:-1; }
      renderProjectList();
    };
    th.onclick=doSort;
    th.onkeydown=e=>{ if(e.key==='Enter'||e.key===' '){ e.preventDefault(); doSort(); } };
    head.appendChild(th);
  }
  // ---- lignes ----
  const list=_projSorted();
  body.innerHTML='';
  for(const b of list){
    const tr=document.createElement('tr');
    tr.className='proj-row'+(b.name===PROJ_CURRENT?' current':'');
    tr.tabIndex=0; tr.setAttribute('role','button'); tr.setAttribute('aria-label', b.name);
    const m=_bundleMetrics(b);
    let cells=`<td class="nm" title="${escHtml(b.name)}">${escHtml(b.name)}</td>`+
      `<td>${escHtml(b.source_clip||'—')}</td>`+
      `<td class="ctr">${b.has_video?'✓':'—'}</td>`+
      `<td class="ctr">${b.has_music?'✓':'—'}</td>`+
      `<td class="ctr">${b.mtime?fmtMtime(b.mtime):'—'}</td>`+
      `<td class="tags-cell"></td>`;   // peuplee ci-dessous (noeud interactif)
    for(const k of metricCols){
      const v=m && m[k];
      // metriques pas encore calculees (job de fond) -> placeholder discret « … »
      const cell=(v==null||isNaN(v))
        ? '<span class="proj-pending" title="'+escHtml(t('col.pending'))+'">…</span>'
        : (+v).toFixed(2);
      cells+=`<td class="ctr metric">${cell}</td>`;
    }
    tr.innerHTML=cells;
    const tagsTd=tr.querySelector('td.tags-cell');
    if(tagsTd) _renderTagsCell(tagsTd, b.name);
    const open=()=>selectProject(b.name);
    tr.onclick=open;
    tr.onkeydown=e=>{ if(e.key==='Enter'||e.key===' '){ e.preventDefault(); open(); } };
    body.appendChild(tr);
  }
  if(cnt) cnt.textContent = list.length
    ? tf('proj.count',{count:list.length})
    : t('proj.none');
}

// ---- tags : suggestions (datalist), cellule editable, filtre ----

// (re)remplit le <datalist id="proj-tags-list"> a partir de PROJ_ALL_TAGS pour
// l'autocompletion des champs « + tag » (un nouveau libelle reste autorise).
function _syncTagDatalist(){
  let dl=$('proj-tags-list');
  if(!dl){
    dl=document.createElement('datalist');
    dl.id='proj-tags-list';
    document.body.appendChild(dl);
  }
  dl.innerHTML='';
  for(const tag of PROJ_ALL_TAGS){
    const o=document.createElement('option');
    o.value=tag;
    dl.appendChild(o);
  }
}

// peuple une cellule « Tags » : chips avec « × » (retrait) + bouton « ＋ tag »
// qui revele un champ (autocomplete via datalist). stopPropagation partout pour
// ne pas declencher le chargement de la ligne.
function _renderTagsCell(td, clip){
  _syncTagDatalist();
  td.innerHTML='';
  td.onclick=e=>e.stopPropagation();      // les clics dans la cellule n'ouvrent pas le projet
  const wrap=document.createElement('div');
  wrap.className='proj-tags';

  const tags=clipTags(clip);
  for(const tag of tags){
    const chip=document.createElement('span');
    chip.className='proj-tag';
    const lbl=document.createElement('span');
    lbl.className='proj-tag-lbl';
    lbl.textContent=tag;
    chip.appendChild(lbl);
    const x=document.createElement('button');
    x.type='button';
    x.className='proj-tag-x';
    x.textContent='×';
    x.title=t('tags.remove');
    x.setAttribute('aria-label', t('tags.remove')+' : '+tag);
    x.onclick=ev=>{
      ev.stopPropagation();
      const next=clipTags(clip).filter(tg=>tg!==tag);
      PROJ_TAGS[clip]=next;            // mise a jour optimiste
      _renderTagsCell(td, clip);
      saveClipTags(clip, next);
    };
    chip.appendChild(x);
    wrap.appendChild(chip);
  }

  // bouton « ＋ tag » -> revele un champ texte (avec autocomplete datalist).
  const add=document.createElement('button');
  add.type='button';
  add.className='proj-tag-add';
  add.textContent=t('tags.add');
  add.title=t('tags.add');
  add.onclick=ev=>{
    ev.stopPropagation();
    add.style.display='none';
    const inp=document.createElement('input');
    inp.type='text';
    inp.className='proj-tag-input';
    inp.setAttribute('list','proj-tags-list');
    inp.placeholder=t('tags.placeholder');
    inp.autocomplete='off';
    const commit=()=>{
      const val=(inp.value||'').trim();
      if(!val){ _renderTagsCell(td, clip); return; }
      const cur=clipTags(clip);
      if(cur.includes(val)){ _renderTagsCell(td, clip); return; }
      const next=cur.concat([val]);
      PROJ_TAGS[clip]=next;            // mise a jour optimiste
      _renderTagsCell(td, clip);
      saveClipTags(clip, next);
    };
    inp.onclick=e2=>e2.stopPropagation();
    inp.onkeydown=e2=>{
      e2.stopPropagation();           // ne pas laisser remonter aux raccourcis globaux
      if(e2.key==='Enter'){ e2.preventDefault(); commit(); }
      else if(e2.key==='Escape'){ e2.preventDefault(); _renderTagsCell(td, clip); }
    };
    inp.onblur=()=>commit();
    wrap.appendChild(inp);
    inp.focus();
  };
  wrap.appendChild(add);

  td.appendChild(wrap);
}

// rendu de la barre de filtre par tag (#proj-tag-filter) : « tous » + une puce
// bascule par tag connu (ANY). N'affiche rien s'il n'existe aucun tag.
function renderTagFilter(){
  const box=$('proj-tag-filter');
  if(!box) return;
  box.innerHTML='';
  if(!PROJ_ALL_TAGS.length){ box.style.display='none'; return; }
  box.style.display='';

  const label=document.createElement('span');
  label.className='proj-tagf-label';
  label.textContent=t('tags.filter');
  box.appendChild(label);

  // « tous » : actif quand aucun tag n'est selectionne -> reinitialise le filtre.
  const all=document.createElement('button');
  all.type='button';
  all.className='proj-tagf-chip'+(PROJ_TAG_FILTER.size?'':' active');
  all.textContent=t('tags.all');
  all.onclick=()=>{ PROJ_TAG_FILTER.clear(); renderTagFilter(); renderProjectList(); };
  box.appendChild(all);

  for(const tag of PROJ_ALL_TAGS){
    const chip=document.createElement('button');
    chip.type='button';
    const on=PROJ_TAG_FILTER.has(tag);
    chip.className='proj-tagf-chip'+(on?' active':'');
    chip.textContent=tag;
    chip.setAttribute('aria-pressed', on?'true':'false');
    chip.onclick=()=>{
      if(PROJ_TAG_FILTER.has(tag)) PROJ_TAG_FILTER.delete(tag);
      else PROJ_TAG_FILTER.add(tag);
      renderTagFilter();
      renderProjectList();
    };
    box.appendChild(chip);
  }
}

// charge un projet par nom + memorise l'index courant pour la nav ◀ ▶.
function selectProject(name){
  PROJ_CURRENT=name;
  loadBundleByName(name);
  renderProjectList();
}

// nav ◀ ▶ : avance/recule dans l'ordre courant (_projOrder) et charge le projet.
function projStep(delta){
  if(!_projOrder.length){ _projSorted(); }
  if(!_projOrder.length) return;
  let i=_projOrder.indexOf(PROJ_CURRENT);
  if(i<0) i = delta>0 ? -1 : 0;          // rien de selectionne -> premier/dernier
  i=(i+delta+_projOrder.length)%_projOrder.length;
  selectProject(_projOrder[i]);
}

// tags d'un clip (tableau, jamais null) — repli sur [] si inconnu.
function clipTags(name){
  const v=PROJ_TAGS[name];
  return Array.isArray(v)? v : [];
}

// (re)charge les tags (GET /tags) dans PROJ_TAGS + PROJ_ALL_TAGS.
async function loadTags(){
  try{
    const r=await fetch('/tags');
    if(!r.ok) throw new Error('/tags '+r.status);
    const j=await r.json();
    PROJ_TAGS=(j && j.tags && typeof j.tags==='object')? j.tags : {};
    PROJ_ALL_TAGS=Array.isArray(j && j.all_tags)? j.all_tags : [];
  }catch(_){
    PROJ_TAGS={}; PROJ_ALL_TAGS=[];
  }
}

// enregistre la liste COMPLETE des tags d'un clip (POST /tags remplace), puis
// met a jour PROJ_TAGS[clip] + PROJ_ALL_TAGS depuis la reponse nettoyee serveur.
async function saveClipTags(clip, tags){
  try{
    const r=await fetch('/tags',{
      method:'POST',
      headers:{'Content-Type':'application/json'},
      body:JSON.stringify({clip, tags}),
    });
    if(!r.ok) throw new Error('/tags '+r.status);
    const j=await r.json();
    const cleaned=Array.isArray(j && j.tags)? j.tags : [];
    if(cleaned.length) PROJ_TAGS[clip]=cleaned; else delete PROJ_TAGS[clip];
    if(Array.isArray(j && j.all_tags)) PROJ_ALL_TAGS=j.all_tags;
  }catch(_){
    // en cas d'echec reseau, on recharge l'etat serveur (verite) pour ne pas mentir.
    await loadTags();
  }
  // retire du filtre tout tag qui n'existe plus nulle part.
  for(const tag of Array.from(PROJ_TAG_FILTER)){
    if(!PROJ_ALL_TAGS.includes(tag)) PROJ_TAG_FILTER.delete(tag);
  }
  renderTagFilter();
  renderProjectList();
}

// (re)charge le workspace + les tags puis re-rend la table (boot + apres imports).
async function refreshProjects(force){
  await Promise.all([loadWorkspace(!!force), loadTags()]);
  renderTagFilter();
  renderProjectList();
}

// ---- config : lit has_metrics + dossiers (GET /get_config). ----
async function loadProjectConfig(){
  try{
    const r=await fetch('/get_config');
    if(!r.ok) return;
    const c=await r.json();
    PROJ_HAS_METRICS=!!c.has_metrics;
    // pre-remplit le panneau Data source (pkl/videos/audio/smpl).
    if($('cfg-data'))   $('cfg-data').value   = c.pkl_dir||'';
    if($('cfg-videos')) $('cfg-videos').value = c.videos_dir||'';
    if($('cfg-audio'))  $('cfg-audio').value  = c.audio_dir||'';
    if($('cfg-smpl'))   $('cfg-smpl').value   = c.smpl_dir||'';
  }catch(_){}
}

// ====================================================================
//  (1) « Charger un fichier » : liste des .pkl bruts (GET /clips),
//  selection -> POST /import_clip -> GET /bundle/load.
// ====================================================================
function openPklPicker(){
  openModal($('pkl-modal'), document.activeElement, $('pkl-search'));
  $('pkl-search').value=''; renderPklList('');
  $('pkl-list').innerHTML=`<div style="padding:12px;color:#8b909c">${t('js.picker.loadlist')}</div>`;
  fetch('/clips').then(r=>r.ok?r.json():Promise.reject(new Error('/clips '+r.status)))
    .then(j=>{ CLIPS=j.clips||[]; $('pkl-count').textContent=tf('pkl.count',{count:CLIPS.length}); renderPklList($('pkl-search').value); })
    .catch(e=>{ $('pkl-list').innerHTML=`<div style="padding:12px;color:#ff7777">${t('js.picker.fail')}${e.message}</div>`; });
}
function closePklPicker(){ closeModal($('pkl-modal')); }
function renderPklList(filter){
  const box=$('pkl-list'); if(!box||!CLIPS) return;
  const f=(filter||'').trim().toLowerCase();
  const matched=(f? CLIPS.filter(c=>c.name.toLowerCase().includes(f)) : CLIPS.slice()).slice(0,400);
  box.innerHTML='';
  for(const c of matched){
    const row=_clipRow();
    const tags=`<span class="tag ${c.has_video?'vid':'novid'}">${c.has_video?t('tag.video'):t('tag.novideo')}</span>`+
      (c.has_music?`<span class="tag corr">♪</span>`:'')+
      (c.converted?'<span class="tag done">.motion</span>':'')+
      (c.mtime?`<span class="clip-date">${fmtMtime(c.mtime)}</span>`:'');
    row.innerHTML=`<span class="nm">${escHtml(c.name)}</span>${tags}`;
    row.setAttribute('aria-label', c.name);
    row.onclick=()=>{ closePklPicker(); importAndLoadClip(c.name); };
    box.appendChild(row);
  }
  if(!matched.length) box.innerHTML=`<div style="padding:12px;color:#8b909c">${CLIPS.length?t('js.picker.nomatch'):t('pkl.none')}</div>`;
}
// convertit un .pkl en .motion (POST /import_clip) puis le charge (GET /bundle/load).
async function importAndLoadClip(name){
  showOverlay(tf('pkl.importing',{name}));
  try{
    const r=await fetch('/import_clip',{method:'POST',
      headers:{'Content-Type':'application/json'}, body:JSON.stringify({name})});
    if(!r.ok) throw new Error('/import_clip — '+await errMsg(r));
    const j=await r.json();
    WORKSPACE=null;                       // la liste a change -> recharge
    await loadBundleByName(j.name||name); // loadBundleByName gere son propre overlay
    await refreshProjects(true);          // le nouveau projet apparait dans la liste
  }catch(e){
    $('status').textContent='✗ '+e.message; $('status').style.color='#ff7777';
    toast(e.message,'err');
  }finally{ hideOverlay(); }
}

// ====================================================================
//  (3) « Charger un dossier » : dialogue 3 dossiers + import de fond.
// ====================================================================
function openFolderDialog(){
  $('folder-status').textContent='';
  $('fm-progress').style.display='none';
  const go=$('folder-go'); if(go) go.disabled=false;
  openModal($('folder-modal'), document.activeElement, $('fm-pkl'));
}
function closeFolderDialog(){ closeModal($('folder-modal')); }

// ====================================================================
//  (C) Job metriques de fond : GET /metrics_status (progression) +
//  POST /metrics_all (relancer). Tant qu'il tourne, on rafraichit le
//  workspace pour que les nouvelles valeurs deviennent triables.
// ====================================================================
function pollMetricsStatus(){
  if(!PROJ_HAS_METRICS) return;          // pas de plugin metriques -> rien a suivre
  if(_metricsPollTimer) clearTimeout(_metricsPollTimer);
  const box=$('proj-metrics-job'), txt=$('proj-metrics-txt');
  let lastRefresh=0;
  const tick=async()=>{
    let j=null;
    try{ const r=await fetch('/metrics_status'); if(r.ok) j=await r.json(); }catch(_){}
    if(!j){ if(box) box.style.display='none'; return; }
    if(j.running){
      if(box) box.style.display='block';
      if(txt) txt.textContent=tf('proj.metrics.job',{
        done:j.done||0, total:j.total||0,
        failed: j.failed? ' · '+j.failed+' échec'+(j.failed>1?'s':'') : '',
      });
      // rafraichit le workspace toutes les ~4 s pour faire apparaitre les valeurs.
      const now=Date.now();
      if(now-lastRefresh>4000){ lastRefresh=now; await loadWorkspace(true); renderProjectList(); }
      _metricsPollTimer=setTimeout(tick,1500);
    }else{
      if(box) box.style.display='none';
      await loadWorkspace(true); renderProjectList();   // dernier rafraichissement
    }
  };
  tick();
}
// bouton « recalculer les métriques » : relance le job de fond.
async function recalcAllMetrics(){
  try{
    const r=await fetch('/metrics_all',{method:'POST'});
    if(!r.ok) throw new Error(await errMsg(r));
    pollMetricsStatus();
  }catch(e){ toast(e.message,'err'); }
}

// ====================================================================
//  (D) Chargement : UNE seule surcouche plein écran à l'ouverture d'un clip.
//  Le HUD multi-spinner historique a été supprimé : setLoadHud() est conservé
//  comme no-op (le préchargement continue silencieusement en tâche de fond).
// ====================================================================
function setLoadHud(/* which, on */){ /* no-op : plus de mini-spinners */ }

// Préchauffe la 1re fenêtre (mailles + fond si affiché) puis se résout. Amorce
// les pompes de préchargement (silencieuses) pour que la lecture démarre
// instantanément ensuite. Garde-fou de temps : ne bloque jamais > ~12 s.
async function warmFirstFrame(){
  // 1) attend la 1re fenetre (maillage + 1er fond) prete, ou 12 s de securite.
  await new Promise(resolve=>{
    if(meshLive && meshVisible()){ meshPrefetchOn=true; pumpMeshPrefetch(); }
    if(bgRemoveActive() && !_serverNoBgFailed){ bgPrefetchOn=true; pumpBgPrefetch(); }
    const t0=performance.now();
    const tick=()=>{
      if(_firstWindowReady() || performance.now()-t0>12000){ resolve(); return; }
      if(meshLive && meshVisible()) pumpMeshPrefetch();
      if(bgRemoveActive() && !_serverNoBgFailed) pumpBgPrefetch();
      setTimeout(tick, 120);
    };
    tick();
  });
  // 2) mise en cache de TOUT le clip, maintenue sous le voile (% + « passer »).
  await gateWholeClipBuffer();
}

// Lance la mise en cache du clip et MAINTIENT le voile jusqu'a 100% (ou clic
// « passer »). Affiche l'avancement dans le voile. Si on passe, le remplissage
// continue en tache de fond. Se debloque aussi au changement de clip (token).
async function gateWholeClipBuffer(){
  if(!CLIP_NAME || !meshLive || !T) return;
  _bufSkip=false;
  bufferWholeClip();                  // demarre le remplissage (incremente le token)
  const tok=meshBufferToken;          // capture APRES (bufferWholeClip a bumpe)
  const skip=$('overlay-skip');
  if(skip){ skip.onclick=()=>{ _bufSkip=true; }; skip.hidden=false; }
  await new Promise(res=>{
    const tick=()=>{
      if(_bufSkip || _bufDone || tok!==meshBufferToken){ res(); return; }
      const m=$('overlay-msg');
      if(m) m.textContent=tf('buffer.gate',{pct:Math.floor(_bufPct)});
      setTimeout(tick, 250);
    };
    tick();
  });
  if(skip) skip.hidden=true;
}

// ---- selecteur de clip ----
// formate un mtime (timestamp epoch en SECONDES, cote serveur) -> 'YYYY-MM-DD HH:MM' local.
function fmtMtime(ts){
  if(ts==null||isNaN(ts)) return '';
  const d=new Date(ts*1000);
  if(isNaN(d.getTime())) return '';
  const p=n=>String(n).padStart(2,'0');
  return `${d.getFullYear()}-${p(d.getMonth()+1)}-${p(d.getDate())} ${p(d.getHours())}:${p(d.getMinutes())}`;
}
// ---- accessibilite des modales : piege le focus, Echap ferme, restaure le focus ----
// Pile des modales ouvertes (la derniere ouverte capte Echap/Tab). Chaque entree
// memorise l'element declencheur pour y rendre le focus a la fermeture.
const _modalStack = [];
function _focusables(el){
  return Array.from(el.querySelectorAll(
    'a[href],button:not([disabled]),input:not([disabled]),select:not([disabled]),'+
    'textarea:not([disabled]),[tabindex]:not([tabindex="-1"])'
  )).filter(n=>n.getClientRects().length>0 || n===document.activeElement);
}
// Rend le reste de la page inerte pour les lecteurs d'ecran/Tab pendant qu'une modale est ouverte.
function _setBackgroundInert(on){
  const bg=$('app');
  if(!bg) return;
  if(on){ bg.setAttribute('aria-hidden','true'); bg.setAttribute('inert',''); }
  else  { bg.removeAttribute('aria-hidden'); bg.removeAttribute('inert'); }
}
function openModal(el, opener, firstFocus){
  el.classList.add('show');
  el.removeAttribute('aria-hidden');
  el._opener = opener || document.activeElement;
  _modalStack.push(el);
  _setBackgroundInert(true);
  const f = firstFocus || _focusables(el)[0];
  if(f) f.focus();
}
function closeModal(el){
  el.classList.remove('show');
  el.setAttribute('aria-hidden','true');
  const i=_modalStack.indexOf(el);
  if(i>=0) _modalStack.splice(i,1);
  if(!_modalStack.length) _setBackgroundInert(false);
  const op=el._opener; el._opener=null;
  if(op && typeof op.focus==='function') op.focus();
}
// gestion clavier globale des modales : Tab piege, Echap ferme la modale du dessus.
document.addEventListener('keydown',e=>{
  if(!_modalStack.length) return;
  const el=_modalStack[_modalStack.length-1];
  // « ? » referme l'aide raccourcis quand elle est au sommet (toggle).
  if(e.key==='?' && el.id==='shortcuts-dialog'){ e.preventDefault(); closeShortcuts(); return; }
  if(e.key==='Escape'){
    e.preventDefault();
    if(el.id==='picker') closePicker();
    else if(el.id==='pkl-modal') closePklPicker();
    else if(el.id==='folder-modal') closeFolderDialog();
    else if(el.id==='src-choice') closeSrcChoice();
    else if(el.id==='confirm-dialog' && typeof el._onEsc==='function') el._onEsc();
    else if(el.id==='shortcuts-dialog') closeShortcuts();
    else if(el.id==='about-dialog') closeAbout();
    else closeModal(el);
    return;
  }
  if(e.key==='Tab'){
    const items=_focusables(el);
    if(!items.length){ e.preventDefault(); return; }
    const first=items[0], last=items[items.length-1];
    const a=document.activeElement;
    if(e.shiftKey && (a===first || !el.contains(a))){ e.preventDefault(); last.focus(); }
    else if(!e.shiftKey && (a===last || !el.contains(a))){ e.preventDefault(); first.focus(); }
  }
},true);

// « Charger un projet » : recherche rapide dans les bundles .motion (workspace).
// La table complete (tri par colonne + nav) reste dans l'onglet Clip.
async function openPicker(){
  openModal($('picker'), document.activeElement, $('picker-search'));
  $('picker-search').value=''; $('picker-search').focus();
  const sortBar=$('picker-sort'); if(sortBar) sortBar.style.display=PROJ_HAS_METRICS?'':'none';
  $('picker-list').innerHTML=`<div style="padding:12px;color:#8b909c">${t('ws.loading')}</div>`;
  await loadWorkspace();
  renderClipList('');
}
function closePicker(){ closeModal($('picker')); }
// Cree une ligne de clip clavier-operable : <button role=option>. Le focus + Enter/Espace
// natifs declenchent onclick ; styling identique grace a la classe .clip-row.
function _clipRow(){
  const row=document.createElement('button');
  row.type='button';
  row.className='clip-row';
  row.setAttribute('role','option');
  return row;
}
function renderClipList(filter){
  // « Charger un projet » : liste workspace-only des bundles .motion. La recherche
  // porte sur nom + clip source ; le tri par metrique (barre du haut) ne s'applique
  // que si un plugin metriques est configure.
  const f=filter.trim().toLowerCase();
  let bundles=(WORKSPACE||[]).slice();
  if(f) bundles=bundles.filter(b=>
    (b.name||'').toLowerCase().includes(f) ||
    (b.source_clip||'').toLowerCase().includes(f));
  const m=(PROJ_HAS_METRICS?SORT_METRIC:'');
  if(m){
    const val=b=>{ const mm=_bundleMetrics(b); const v=mm&&mm[m]; return (v==null||isNaN(v))? null : +v; };
    bundles.sort((a,b)=>{
      const va=val(a), vb=val(b);
      if(va==null&&vb==null) return 0;
      if(va==null) return 1;          // valeur manquante -> en fin
      if(vb==null) return -1;
      return vb-va;                   // pire (plus grand) d'abord
    });
  }
  bundles=bundles.slice(0,400);
  const box=$('picker-list');
  box.innerHTML='';
  for(const b of bundles){
    const row=_clipRow();
    const tags=`<span class="tag corr">${t('tag.bundle')}</span>`+
      `<span class="tag ${b.has_video?'vid':'novid'}">${b.has_video?t('tag.video'):t('tag.novideo')}</span>`+
      (b.mtime?`<span class="clip-date">${fmtMtime(b.mtime)}</span>`:'');
    let mval='';
    if(m){
      const mm=_bundleMetrics(b); const v=mm&&mm[m];
      mval=`<span class="mval">${(v==null||isNaN(v))? '—' : _metricLabel(m)+' '+(+v).toFixed(1)}</span>`;
    }
    row.innerHTML=`<span class="nm">${escHtml(b.name)}</span>${tags}${mval}`;
    row.setAttribute('aria-label', b.name);
    row.onclick=()=>{ closePicker(); selectProject(b.name); };
    box.appendChild(row);
  }
  $('picker-count').textContent=tf('proj.count',{count:bundles.length});
  if(!bundles.length) box.innerHTML=`<div style="padding:12px;color:#8b909c">${t('proj.none')}</div>`;
}
// modale : clip corrige -> choix « ouvrir l'original » vs « ouvrir la version corrigee »
function askSource(name, origSrc, corrSrc){
  origSrc = origSrc || 'original';
  corrSrc = corrSrc || 'corrected';
  $('src-choice-name').textContent=name;
  const choose=src=>{ closeSrcChoice(); closePicker(); loadClipByName(name, src); };
  $('src-open-original').onclick=()=>choose(origSrc);
  $('src-open-corrected').onclick=()=>choose(corrSrc);
  openModal($('src-choice'), document.activeElement, $('src-open-original'));
}
function closeSrcChoice(){ closeModal($('src-choice')); }
function bindPicker(){
  $('picker-close').onclick=closePicker;
  $('picker-search').oninput=e=>renderClipList(e.target.value);
  $('picker').addEventListener('click',e=>{ if(e.target.id==='picker') closePicker(); });
  // modale choix source (conservee pour compat ; non utilisee par la liste projet)
  if($('src-choice-cancel')){
    $('src-choice-cancel').onclick=closeSrcChoice;
    $('src-choice').addEventListener('click',e=>{ if(e.target.id==='src-choice') closeSrcChoice(); });
  }
  // barre de tri par metrique : masquee si aucun plugin metriques configure.
  const sortBar=$('picker-sort'); if(sortBar) sortBar.style.display=PROJ_HAS_METRICS?'':'none';
  // barre de tri : A→Z (data-sort vide) ou tri decroissant par metrique
  document.querySelectorAll('#picker-sort .sort-btn').forEach(btn=>{
    btn.onclick=()=>{
      SORT_METRIC=btn.getAttribute('data-sort')||'';
      document.querySelectorAll('#picker-sort .sort-btn').forEach(b=>b.classList.remove('active'));
      btn.classList.add('active');
      renderClipList($('picker-search').value);
    };
  });
}

let last=0;
function animate(t){
  requestAnimationFrame(animate);
  if(playing && DATA){
    const au=$('music');
    const audioWanted = musicEnabled && DATA.has_music && au && !au.muted;
    // si le son est voulu mais l'<audio> s'est mis en pause (fin de buffer /
    // rebouclage), on le relance au lieu de retomber en lecture silencieuse.
    if(audioWanted && au.paused){ const p=au.play(); if(p&&p.catch) p.catch(()=>{}); }
    const audioDriving = audioWanted && au && !au.paused;
    if(audioDriving){
      // l'audio mene : la frame suit le temps de lecture (image collee au son).
      const f = Math.floor((au.currentTime||0) * fpsVal());
      if(f>=T){ au.currentTime=0; setFrame(0); }      // boucle propre (au.loop gere le son)
      else if(f!==curFrame){ setFrame(f); }
    }else if(t-last > 1000/fpsVal()){
      last=t; setFrame((curFrame+1)%T);
    }
  }
  orbit.update();
  renderer.render(scene,camera);
}
function resize(){
  const v=$('view'); camera.aspect=v.clientWidth/v.clientHeight;
  camera.updateProjectionMatrix(); renderer.setSize(v.clientWidth,v.clientHeight);
}

// expose pour smoke-test headless
window.__POSE_EDITOR__ = { get ready(){return !!DATA;}, get N(){return N;},
  get T(){return T;}, get J(){return J;}, setFrame, exportData(){return {N,T,J,fps:DATA.fps,parents:DATA.parents,joints:Array.from(edited)};},
  selectDancer(n){ selDancer=n; const sd=$('sel-d'); if(sd) sd.value=n; updateSwatch(); attachGizmo(); updateJointFields(); },
  moveDancer(dx,dy,dz,allFrames){ moveDancer(dx,dy,dz,!!allFrames); },
  moveDancerCmd(dx,dy,dz){ moveDancerCmd(dx,dy,dz); },
  getJoint(n,t,j){ const b=idx(n,t,j); return [edited[b],edited[b+1],edited[b+2]]; },
  setJoint(n,t,j,x,y,z){ const b=idx(n,t,j); edited[b]=x;edited[b+1]=y;edited[b+2]=z; if(t===curFrame) refreshDancerVisual(n); },
  setJointCmd(n,t,j,x,y,z){ const b=idx(n,t,j); const before=[edited[b],edited[b+1],edited[b+2]];
    edited[b]=x;edited[b+1]=y;edited[b+2]=z; pushCmd({type:'joint',n,t,j,before,after:[x,y,z]});
    if(t===curFrame) refreshDancerVisual(n); },
  undo(){ undo(); }, redo(){ redo(); },
  get undoLen(){ return undoStack.length; }, get redoLen(){ return redoStack.length; },
  setLang(l){ applyLang(l); }, get lang(){ return LANG; },
  setTab(name){ setTab(name); },
  get floor(){ return DATA && DATA.floor || null; },
  get floorVisible(){ return !!(floorGrid && floorGrid.visible); },
  setFloorVisible(v){ setFloorOnChecked(!!v); if(floorGrid) floorGrid.visible=!!v; },
  get floorToggleOn(){ return floorOnChecked(); },
  // --- hooks correction du sol ---
  get floors(){ return DATA && DATA.floors || null; },
  get floorPlane(){ return floorPlane ? floorPlane.slice() : null; },
  get floorVariant(){ return floorVariant; },
  selectFloorVariant(name){ selectFloorVariant(name); },
  get floorEditMode(){ return floorEditMode; },
  setFloorEditMode(v){ setFloorEditMode(!!v); },
  setFloorFields(txDeg,tyDeg,h){ $('floor-tx').value=txDeg; $('floor-ty').value=tyDeg; $('floor-h').value=h; applyFloorFields(); },
  get floorTiltDeg(){ return floorPlane ? floorTiltDeg(floorPlane) : null; },
  saveFloor(){ return saveFloor(); },
  recomputeFloor(){ return recomputeFloor(); },
  get floorRecomputeStatus(){ return $('floor-recompute-status').textContent; },
  get floorSaveStatus(){ return $('floor-save-status').textContent; },
  get floorGizmoAttached(){ return !!(floorGrid && tcontrols.object===floorGrid); },
  // --- hooks distance au sol (smoke-test) ---
  get floorDistOn(){ return floorDistOn; },
  get floorDistDisabled(){ return !!($('floor-dist') && $('floor-dist').disabled); },
  setFloorDist(v){ return setFloorDist(!!v); },
  get floorDistCount(){ return floorDistLines.length; },
  // couleur (hex) + distance signee de chaque trait : [{color, signed, above}]
  floorDistLines(){ return floorDistLines.map(l=>({
    color: l.material.color.getHex(),
    signed: l.userData.signed,
    above: l.userData.signed>0,
  })); },
  async fetchFootMasks(){ const m=await ensureFootMasks(); return m?{left:m.left.length,right:m.right.length}:null; },
  refit(frames){ return doRefit(frames); },
  get meshCount(){ return meshObjs.length; },
  get meshLive(){ return meshLive; },
  get meshVisible(){ return meshVisible(); },
  toggleMesh(){ return toggleMesh(); },
  get curFrame(){ return curFrame; },
  // --- hooks read-only pour le smoke-test du maillage en lecture ---
  get meshCacheSize(){ return meshCache.size; },
  get meshInflightSize(){ return meshInflight.size; },
  get meshPrefetchOn(){ return meshPrefetchOn; },
  get playing(){ return playing; },
  setPlaying(v){ playing=!!v; $('play').textContent=playing?'❚❚':'▶'; $('play').classList.toggle('on',playing); syncMeshPrefetch(); syncMusicPlayback(); },
  meshVert0(){ if(!meshObjs.length) return null; const a=meshObjs[0].geometry.attributes.position.array; return [a[0],a[1],a[2]]; },
  get clipName(){ return CLIP_NAME; },
  get clipSource(){ return CLIP_SOURCE; },
  get hasVideo(){ return !!bg; },
  // --- hooks read-only pour les tests rendu (opacite/echelle fond, ombres, vues) ---
  get bgOpacity(){ if(!bg) return null; return (bg.material.uniforms && bg.material.uniforms.opacity !== undefined) ? bg.material.uniforms.opacity.value : bg.material.opacity; },
  get bgScale(){ return bg ? bg.scale.x : null; },
  setView(which){ setView(which); },
  cameraPos(){ return [camera.position.x, camera.position.y, camera.position.z]; },
  get shadowMapEnabled(){ return !!(renderer && renderer.shadowMap.enabled); },
  get shadowFloorPresent(){ return !!shadowFloor; },
  get meshShadowFlags(){ return meshObjs.map(m=>({cast:m.castShadow, receive:m.receiveShadow, opacity:m.material.opacity, roughness:m.material.roughness})); },
  // --- hooks reglage temporel du fond (smoke-test) ---
  get bgOffset(){ return DATA ? DATA.bg_offset : null; },
  get bgVideoDuration(){ return DATA ? DATA.video_duration : null; },
  get bgClipDuration(){ return DATA ? DATA.clip_duration : null; },
  get bgTimeMax(){ return bgTimeMax(); },
  get bgTimeVal(){ return bgTimeVal(); },
  setBgTimeVal(v){ setBGTimeVal(v); },
  get bgVersion(){ return bgVersion; },
  reextractBg(){ return reextractBg(); },
  get bgStatus(){ return $('bg-t-status').textContent; },
  // --- hooks metriques (clip entier) + maillage live (smoke-test) ---
  get metricsPanelShown(){ return $('metrics-panel').classList.contains('show'); },
  get metricsRef(){ return metricsRef; },
  get metricsCur(){ return metricsCur; },
  get metricsDirty(){ return metricsDirty; },
  get meshShown(){ return meshShouldBeLive(); },
  liveRefitMesh(){ return liveRefitMesh(); },
  recomputeClipMetrics(){ return recomputeClipMetrics(); },
  get liveBusy(){ return liveBusy; },
  // --- hooks translation pure (smoke-test du fix pieds) ---
  dancerRigid(n){ const r=dancerRigidOffset(n); return {rigid:r.rigid, edits:!!r.edits,
    off: r.rigid? Array.from(r.off.subarray(curFrame*3, curFrame*3+3)) : null}; },
  // verts (x,y,z) d'un sommet du maillage affiche pour le danseur n
  meshVertN(n,k){ if(!meshObjs[n]) return null; const a=meshObjs[n].geometry.attributes.position.array;
    return [a[k*3],a[k*3+1],a[k*3+2]]; },
  get mpStatus(){ return $('mp-status').textContent; },
  loadByName(name, source){ return loadClipByName(name, source); },
  // --- hooks musique (smoke-test) ---
  get hasMusic(){ return !!(DATA && DATA.has_music); },
  get musicEnabled(){ return musicEnabled; },
  get musicSrc(){ const a=$('music'); return a ? (a.getAttribute('src')||'') : ''; },
  get musicCurrentTime(){ const a=$('music'); return a ? (a.currentTime||0) : 0; },
  get musicPaused(){ const a=$('music'); return a ? a.paused : true; },
  toggleMusic(){ return toggleMusic(); },
  // --- hooks etirement du deplacement (points cibles du bassin) ---
  get stretchMode(){ return stretchMode; },
  setStretchMode(v){ setStretchMode(!!v); },
  stretchPts(n){ return (stretchPts[n]||[]).map(p=>({f:p.f,x:p.x,y:p.y,z:p.z})); },
  stretchOffset(n,t){ return stretchOffset(n,t); },
  pelvisOrig(n,t,axis){ return pelvisOrig(n,t,axis); },
  // pose un point cible a la frame f (cible absolue donnee) en commande undo
  stretchSetPt(n,f,x,y,z){ selDancer=n; $('sel-d').value=n; setFrame(f); stretchSetPtCmd(n,f,x,y,z); },
  // ancre a la frame f (cible = position originale du bassin)
  stretchAnchor(n,f){ selDancer=n; $('sel-d').value=n; setFrame(f);
    stretchSetPtCmd(n,f, pelvisOrig(n,f,0), pelvisOrig(n,f,1), pelvisOrig(n,f,2)); },
  stretchClear(n){ if(stretchPts[n]&&stretchPts[n].length){ const before=stretchSnapshot(n); stretchPts[n]=[];
    recomposeDancer(n); pushCmd({type:'stretch',n,before,after:[]}); refreshDancerVisual(n); setFrame(curFrame); renderStretchPanel(); } },
  // --- hook BUG 1 : offset constant cumule du danseur courant (champs g-*-val) ---
  get globalFields(){ return { x:parseFloat($('g-x-val').textContent), y:parseFloat($('g-y-val').textContent), z:parseFloat($('g-z-val').textContent) }; },
  // --- hooks sauvegarde / export (cartouche en haut) ---
  get saveDirty(){ return saveDirty; },
  get savePillText(){ return $('save-pill-txt').textContent; },
  get savePillSaved(){ return $('save-pill').classList.contains('saved'); },
  get saveStatus(){ return $('save-status').textContent; },
  exportPkl(){ return exportPkl(); },
  get currentTab(){ return localStorage.getItem('pe.tab'); },
  // hook test : recupere les octets pkl du /export_pkl en base64 (validation pickle)
  async exportPklBytesB64(){
    const body={ N, T, J, joints:Array.from(edited), source:CLIP_SOURCE };
    const r=await fetch(`/export_pkl?clip=${encodeURIComponent(CLIP_NAME)}&source=${encodeURIComponent(CLIP_SOURCE)}`,
      {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify(body)});
    const buf=new Uint8Array(await r.arrayBuffer());
    let bin=''; for(let i=0;i<buf.length;i++) bin+=String.fromCharCode(buf[i]);
    return { status:r.status, ctype:r.headers.get('Content-Type'),
      disp:r.headers.get('Content-Disposition'), b64:btoa(bin), N, T, J };
  },
  // --- hooks commentaires (smoke-test) ---
  get commentsDisabled(){ return commentsDisabled(); },
  get comments(){ return commentsList.map(c=>({user:c.user,text:c.text,time:c.time})); },
  get commentCount(){ return commentsList.length; },
  get commentUser(){ const u=$('comment-user'); return u?u.value:''; },
  setCommentUser(v){ const u=$('comment-user'); if(u) u.value=v; if(v) localStorage.setItem('pe.user', v); },
  setCommentText(v){ const ti=$('comment-text'); if(ti) ti.value=v; },
  loadComments(){ return loadComments(); },
  sendComment(){ return sendComment(); },
  get commentStatus(){ const s=$('comment-status'); return s?s.textContent:''; },
  // bundles .motion / workspace / dossiers (nouveau)
  saveBundle, loadBundleByName, importFolder, loadWorkspace,
  get workspace(){ return WORKSPACE; },
  openPicker, savePkl,
  // --- liste unifiee des projets + chargement (smoke-test) ---
  openPklPicker, openFolderDialog,
  refreshProjects, renderProjectList, selectProject, projStep,
  // --- tags libres par clip (smoke-test) ---
  clipTags, renderTagFilter,
  get projAllTags(){ return PROJ_ALL_TAGS.slice(); },
  get projTagFilter(){ return Array.from(PROJ_TAG_FILTER); },
  setTagFilter(tags){ PROJ_TAG_FILTER=new Set(tags||[]); renderTagFilter(); renderProjectList(); },
  get projOrder(){ return _projOrder.slice(); },
  get projCurrent(){ return PROJ_CURRENT; },
  get hasMetrics(){ return PROJ_HAS_METRICS; },
  setProjSort(key){ PROJ_SORT_KEY=key; PROJ_SORT_DIR=1; renderProjectList(); },
  get projSortKey(){ return PROJ_SORT_KEY; },
  // --- indicateurs de chargement (smoke-test) ---
  get loadHud(){ return Object.assign({}, _loadHud); },
  prewarmBg };


// ---- panneau Source : regler data/videos/smpl en direct (persiste, zero CLI) ----
async function applyConfig(){
  const body={ pkl_dir:$('cfg-data').value.trim(),
               videos_dir:$('cfg-videos').value.trim(),
               audio_dir:($('cfg-audio')?$('cfg-audio').value.trim():''),
               smpl_dir:$('cfg-smpl').value.trim() };
  const s=$('cfg-status'); s.style.color='#e7c14b'; s.textContent='\u2026';
  try{
    const r=await fetch('/set_config',{method:'POST',
      headers:{'Content-Type':'application/json'}, body:JSON.stringify(body)});
    const j=await r.json();
    if(!r.ok) throw new Error(j.error||('HTTP '+r.status));
    const n=(j.n_pkl!=null?j.n_pkl:j.n_clips);
    s.style.color='#7fd18b'; s.textContent=tf('settings.data.applied',{pkl:n, proj:(j.n_bundles!=null?j.n_bundles:0)});
    CLIPS=null; WORKSPACE=null;          // la source a change -> recharge tout
    await refreshProjects(true);
    await loadProjectConfig();           // r\u00e9-\u00e9value has_metrics
    if(typeof toast==='function') toast(n+' pkl', 'info');
  }catch(e){ s.style.color='#ff8a8a'; s.textContent='\u2717 '+e.message; }
}

let _browseTarget=null, _browsePath=null;
function openBrowse(inputId){ _browseTarget=inputId; $('browse-modal').style.display='flex';
  browseTo($(inputId).value.trim()); }
function closeBrowse(){ $('browse-modal').style.display='none'; }
function chooseBrowse(){ if(_browseTarget && _browsePath) $(_browseTarget).value=_browsePath; closeBrowse(); }
async function browseTo(path){
  const cur=$('browse-cur'), list=$('browse-list');
  try{
    const r=await fetch('/list_dir?path='+encodeURIComponent(path||''));
    const j=await r.json();
    if(!r.ok){ cur.textContent=j.error||t('browse.error'); return; }
    _browsePath=j.path;
    cur.textContent=j.path+(j.is_dataset?'   '+t('browse.dataset'):'');
    let html='';
    if(j.parent) html+='<div class="browse-row" data-p="'+escHtml(j.parent)+'">\uD83D\uDCC1 ..</div>';
    for(const d of j.dirs){
      const full=j.path.replace(/\/$/,'')+'/'+d;
      html+='<div class="browse-row" data-p="'+escHtml(full)+'">\uD83D\uDCC1 '+escHtml(d)+'</div>';
    }
    list.innerHTML=html||('<div class="small" style="padding:8px">'+escHtml(t('browse.empty'))+'</div>');
    list.querySelectorAll('.browse-row').forEach(el=>{ el.onclick=()=>browseTo(el.getAttribute('data-p')); });
  }catch(e){ cur.textContent=t('browse.error')+': '+e.message; }
}
init();
