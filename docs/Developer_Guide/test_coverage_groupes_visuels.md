# Couverture des tests — groupes visuels

Ce document recense les **77 tests** dédiés aux groupes visuels, répartis en **8 fichiers** sous `tests/gui/`.

---

## Synthèse

| Fichier | Tests | Domaine principal |
|---------|------:|-------------------|
| `test_visual_group_controller.py` | 8 | Logique contrôleur (CRUD groupe, membres, frontières) |
| `test_visual_group_view.py` | 14 | Vue, navigation, raccourcis, proxies, undo layout |
| `test_visual_group_persistence.py` | 4 | Sérialisation YAML (save/load, rétrocompatibilité) |
| `test_nested_visual_groups.py` | 8 | Hiérarchie imbriquée, visibilité, suppression |
| `test_group_orientation.py` | 3 | Ctrl+R sur groupe et proxy In/Out |
| `test_group_boundary_labels.py` | 4 | Libellés des ports de frontière |
| `test_diagram_clipboard.py` | 8 | Copier-coller blocs, groupes, proxies |
| `test_manual_boundary_wiring.py` | 28 | Câblage partiel, fils `---`, reconnexion (In **et** Out) |
| **Total** | **77** | |

---

## `test_visual_group_controller.py`

Logique `ProjectController` : création, suppression, appartenance, frontières auto.

| Test | Cas couvert |
|------|-------------|
| `test_group_blocks_creates_visual_group_with_boundaries` | Groupage de 2 blocs avec connexion interne + sortie vers l'extérieur ; frontière auto de direction `output` |
| `test_ungroup_removes_visual_group` | Dé-groupement supprime l'entité ; `ungroup` sur uid absent retourne `False` |
| `test_remove_block_updates_group_membership` | `remove_block` retire le membre du groupe ; groupe supprimé quand vide |
| `test_add_block_to_group_moves_membership` | `add_block_to_group` ajoute un bloc existant au groupe (undoable) |
| `test_add_block_in_group_view_creates_member` | Drop palette en vue interne (`add_block_in_group_view`) crée et ajoute le bloc |
| `test_remove_block_from_group_keeps_block_visible_at_parent` | `remove_block_from_group` retire le membre sans supprimer le bloc ; réaffichage au parent |
| `test_cannot_add_block_already_owned_by_another_group` | Un bloc déjà membre d'un groupe ne peut pas être ajouté à un autre |
| `test_boundary_ports_recomputed_when_connections_change` | Ajout d'une connexion traversante → nouvelle frontière `input` ; suppression → frontière orpheline conservée (uid membre, pas de `linked_connection_uid`) |

---

## `test_visual_group_view.py`

Interaction `DiagramView` : visibilité, navigation, raccourcis, proxies, ports manuels.

| Test | Cas couvert |
|------|-------------|
| `test_group_hides_members_and_shows_group_item` | Au niveau racine : membres masqués, `GroupItem` visible, blocs externes visibles |
| `test_group_captures_member_layouts_and_internal_view_applies_them` | Positions capturées au groupage ; restaurées en vue interne ; sauvegardées à la sortie |
| `test_double_click_enters_group_view` | Entrée dans le groupe : membres visibles, rectangle groupe masqué |
| `test_keyboard_shortcut_groups_selection` | `Ctrl+Shift+G` groupe la sélection |
| `test_keyboard_shortcut_ungroups_selection` | `Ctrl+Shift+U` dé-groupe le groupe sélectionné ; membres réaffichés |
| `test_undo_redo_move_resize_group` | Déplacement/redimensionnement du rectangle groupe (undo/redo) |
| `test_redo_move_resize_after_redo_group_keeps_same_uid` | Undo group + undo move, puis redo : même `uid` de groupe, move rejoué correctement |
| `test_group_boundary_proxies_assigned_on_creation` | Chaque frontière a un `proxy_uid` et un `proxy_layout` à la création |
| `test_proxies_visible_only_in_internal_view` | Proxies In/Out masqués à la racine, visibles en vue interne |
| `test_palette_exposes_group_ports_in_internal_view` | Catégorie `group_ports` (In/Out) visible uniquement en vue interne |
| `test_add_manual_boundary_port_creates_proxy` | Ajout port manuel `input` → proxy visible, label `In`, position sauvegardée |
| `test_add_second_manual_in_gets_unique_name` | Deuxième In nommé `In_1` ; labels affichés sur le rectangle parent |
| `test_undo_removes_manual_ports_before_ungrouping` | Undo port manuel puis undo groupage dans le bon ordre |
| `test_undo_connection_route_edit` | Undo/redo édition de route de connexion *(hors groupes — test de régression undo général)* |

---

## `test_visual_group_persistence.py`

Persistance `gui.groups` dans `project.yaml`.

| Test | Cas couvert |
|------|-------------|
| `test_visual_group_from_dict_preserves_group_layout_with_member_layouts` | Désérialisation unitaire `VisualGroup.from_dict` (layout groupe + `member_layouts`) |
| `test_build_project_yaml_includes_gui_groups` | `build_project_yaml` écrit `gui.groups` avec frontières manuelles et layouts |
| `test_loader_restores_visual_groups_from_yaml` | Chargement projet avec groupes : uid, frontière manuelle, `member_layouts` |
| `test_loader_keeps_backward_compatibility_without_gui_groups` | Projet sans `gui.groups` → liste vide, pas d'erreur |

---

## `test_nested_visual_groups.py`

Groupes parents/enfants, visibilité multi-niveaux, suppression récursive.

| Test | Cas couvert |
|------|-------------|
| `test_group_block_with_existing_subgroup` | Grouper un bloc + un sous-groupe existant : `child_group_uids`, `parent_uid` |
| `test_nested_group_visibility_at_root_and_inside_parent` | Masquage récursif à la racine ; enfant visible dans le parent |
| `test_group_selected_block_and_subgroup_from_context_menu` | Sélection bloc + `GroupItem` → groupage avec sous-groupe enfant |
| `test_ungroup_parent_promotes_child_groups` | Dé-grouper le parent promeut les enfants à la racine (`parent_uid = null`) |
| `test_create_subgroup_inside_parent_view` | Création sous-groupe depuis la vue interne du parent |
| `test_cross_group_connection_visible_at_root` | Connexion entre deux groupes frères visible à la racine |
| `test_cross_child_connection_visible_inside_parent` | Connexion entre enfants masquée à la racine, visible dans le parent |
| `test_delete_group_removes_nested_members_and_child_groups` | `delete_group` sur boucle imbriquée supprime blocs + sous-groupes ; undo restaure |

---

## `test_group_orientation.py`

Retournement visuel `Ctrl+R` sans modifier les blocs membres.

| Test | Cas couvert |
|------|-------------|
| `test_ctrl_r_flips_group_display_without_touching_members` | Ports de frontière inversés (`normal` → `flipped`) ; orientation des membres inchangée |
| `test_flipped_group_wire_exits_away_from_anchor` | Routage fil externe : segment sort du rectangle dans le bon sens après flip |
| `test_ctrl_r_flips_proxy_display_without_touching_members` | Flip proxy In/Out en vue interne ; membre non retourné |

---

## `test_group_boundary_labels.py`

Libellés affichés sur les ports de frontière (`group_boundary_labels.py`).

| Test | Cas couvert |
|------|-------------|
| `test_boundary_port_label_input_shows_external_source` | Frontière auto entrée → label = `display_as` du bloc source externe |
| `test_boundary_port_label_output_shows_external_destination` | Frontière auto sortie → label = `display_as` du bloc destination externe |
| `test_boundary_port_label_manual_defaults_to_in_or_out` | Port manuel sans câblage → `In` / `Out` |
| `test_boundary_port_label_manual_keeps_proxy_name_when_internally_wired` | Port manuel câblé en interne garde le label proxy (`In`) |

---

## `test_diagram_clipboard.py`

Copier-coller via `diagram_clipboard.py`.

| Test | Cas couvert |
|------|-------------|
| `test_copy_paste_nested_group_preserves_hierarchy` | Copier boucle imbriquée → 3 groupes, 4 blocs, noms suffixés `_1`, hiérarchie préservée |
| `test_copy_paste_multiple_root_groups` | Copier deux groupes racine → deux racines collées avec noms uniques |
| `test_copy_paste_blocks_only` | Copier blocs + connexion sans groupe |
| `test_paste_nested_group_undo` | `undo_paste` annule duplication imbriquée |
| `test_paste_group_inside_parent_view` | Coller un sous-groupe dans la vue parent → `parent_uid` correct |
| `test_copy_paste_manual_in_out_proxies` | Copier/coller proxies In/Out avec positions et labels uniques |
| `test_copy_paste_proxy_with_member_block_preserves_internal_link` | Copier proxy + bloc membre → `linked_port_uid` recâblé sur le nouveau bloc |
| `test_paste_proxies_requires_internal_group_view` | Coller proxies hors vue interne refusé (`paste_clipboard_at` → `False`) |

---

## `test_manual_boundary_wiring.py`

Câblage partiel des frontières auto et manuelles, fils en pointillés, reconnexion côté par côté.

| Test | Cas couvert |
|------|-------------|
| `test_delete_incomplete_internal_boundary_wire_keeps_proxy` | Suppression fil interne manuel (In) → proxy conservé, `linked_port_uid` vidé |
| `test_delete_incomplete_internal_boundary_wire_keeps_output_proxy` | Même scénario pour proxy **Out** (câblage `gain.output` ↔ GroupOut) |
| `test_delete_incomplete_external_boundary_wire_keeps_group_port` | Suppression fil externe après câblage partiel (In) → état externe vidé, interne conservé |
| `test_delete_incomplete_external_boundary_wire_keeps_output_group_port` | Même scénario pour proxy **Out** (externe sur `sum.input`) |
| `test_delete_completed_group_connection_keeps_proxy_and_shows_dashed_wire` | Suppression connexion complète (In) → fil interne `---`, pas de fil externe à la racine |
| `test_delete_completed_group_connection_keeps_output_proxy_and_dashed_wire` | Même scénario pour proxy **Out** |
| `test_delete_block_to_group_connection_keeps_internal_dashed_wire` | Suppression fil auto entrée à la racine → frontière orpheline + fil interne `---` |
| `test_delete_block_to_group_output_connection_keeps_internal_dashed_wire` | Même scénario pour frontière auto **sortie** |
| `test_delete_inside_group_keeps_external_reconnect_state` | Suppression fil interne auto (entrée) → fil externe `---` ; reconnexion externe puis interne |
| `test_delete_inside_group_keeps_external_reconnect_state_for_output` | Même scénario pour frontière auto **sortie** |
| `test_delete_internal_dashed_after_root_delete_keeps_nothing` | Suppression fil interne (In) après déconnexion racine → état entièrement vidé |
| `test_delete_internal_dashed_after_root_delete_keeps_nothing_for_output` | Même scénario pour proxy **Out** |
| `test_delete_auto_boundary_connection_keeps_proxy_in_group_view` | Suppression fil auto entrée → proxy visible + fil interne `---` |
| `test_delete_auto_output_boundary_connection_keeps_proxy_in_group_view` | Même scénario pour frontière auto **sortie** |
| `test_reconnect_block_to_group_via_border_port` | Reconnexion externe via port rectangle après suppression |
| `test_reconnect_after_delete_via_boundary_ports` | Reconnexion directe bloc↔bloc restaure `linked_connection_uid` |
| `test_cross_group_delete_keeps_border_ports_without_dashed_wires` | Suppression fil entre deux groupes → ports conservés, pas de fils `---` à la racine |
| `test_cross_group_reconnect_via_group_boundary_ports` | Reconnexion port sortie groupe A → port entrée groupe B |
| `test_auto_boundary_internal_dashed_after_cross_group_delete` | Après suppression cross-group → fil interne `---` visible dans le groupe source |
| `test_parent_group_shows_proxies_for_child_boundaries` | Proxies parent pour frontières enfant (y compris imbriqué) |
| `test_parent_with_only_child_groups_shows_proxies` | Groupe sans membres directs, uniquement enfants → tous les proxies visibles |
| `test_cross_child_group_delete_and_reconnect_inside_parent` | Suppression/reconnexion entre enfants depuis la vue parent |
| `test_delete_inside_nested_group_preserves_parent_external` | Suppression fil dans sous-groupe → état externe parent préservé + fil `---` racine |
| `test_reconnect_inside_nested_group_after_delete` | Reconnexion interne dans sous-groupe imbriqué |
| `test_reconnect_outside_nested_group_after_delete` | Reconnexion externe parent puis interne enfant (2 étapes) |
| `test_group_border_ports_keep_vertical_order_after_rebuild` | Ordre vertical des ports conservé après `_rebuild_group_boundary_ports` |
| `test_cross_group_delete_does_not_spawn_multiple_root_dashed_wires` | Pas de fils `---` parasites à la racine après suppression cross-group |
| `test_proxy_wires_to_child_group_border_inside_parent` | Proxy parent câblé vers port frontière d'un groupe enfant |

---

## Commande de vérification

```bash
python -m pytest tests/gui/test_visual_group*.py \
    tests/gui/test_group*.py \
    tests/gui/test_manual_boundary_wiring.py \
    tests/gui/test_diagram_clipboard.py \
    tests/gui/test_nested_visual_groups.py -v

python -m pytest tests/ -q
```

### Sans affichage (offscreen / CI)

```bash
QT_QPA_PLATFORM=offscreen python -m pytest tests/gui/test_visual_group*.py \
    tests/gui/test_group*.py \
    tests/gui/test_manual_boundary_wiring.py \
    tests/gui/test_diagram_clipboard.py \
    tests/gui/test_nested_visual_groups.py -v

QT_QPA_PLATFORM=offscreen python -m pytest tests/ -q
```
