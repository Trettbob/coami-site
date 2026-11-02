# Mutation verification

Run `python3 -I -B scripts/test_mutants.py`. Each mutant starts from a fresh
temporary copy, first passes its focused baseline, then must cause an assertion
failure in the named regression. Runtime/import/syntax errors never count.
The exact source edits live in `scripts/test_mutants.py`.

M01–M169 are retained. M170–M200 cover whole-page pins, element boundaries,
visibility, integration, and preservation of the original joined-word ban.
M115 removes the shared aria-hidden copy guard for both text scans.
M201 restores the closing section's duplicate resolved name; M202 removes
reduced motion from the emitted accessibility config.
M203 moves the glow back onto a content-bearing hero; M204 removes its stacking
isolation; M205 brings the glow up to the content layer; M206 incorrectly treats
the negative decorative layer as hiding content.

| Mutant / check removed | File | Required regression |
| --- | --- | --- |
| M01 DTD lexical guard | `scripts/site_common.py` | `test_r4_dtd_entities` |
| M02 entity-reference guard | `scripts/site_common.py` | `test_r4_entities_html_and_svg` |
| M03 XML parser DTD refusal | `scripts/site_common.py` | `test_r4_xml_parser_refuses_dtd` |
| M04 XML parser selection | `scripts/site_common.py` | `test_r4_svg_xml_well_formed` |
| M05 XML root namespace | `scripts/site_common.py` | `test_r4_svg_xml_allowlist` |
| M06 XML element allowlist | `scripts/site_common.py` | `test_r4_svg_xml_allowlist` |
| M07 XML attribute allowlist | `scripts/site_common.py` | `test_r4_svg_xml_allowlist` |
| M08 inline SVG element allowlist | `scripts/check_no_third_party.py` | `test_r4_inline_svg_allowlist` |
| M09 inline SVG attribute allowlist | `scripts/check_no_third_party.py` | `test_r4_inline_svg_allowlist` |
| M10 URL in arbitrary attribute | `scripts/check_no_third_party.py` | `test_r4_attribute_urls` |
| M11 restrict navigation exception | `scripts/check_no_third_party.py` | `test_r4_non_navigation_hrefs` |
| M12 duplicate HTML attributes | `scripts/site_common.py` | `test_r4_duplicate_attributes` |
| M13 inline validator directives | `scripts/site_common.py` | `test_r4_validator_directives` |
| M14 CI preflight | `scripts/ci_checks.py` | `test_r4_ci_markup_preflight` |
| M15 Legal forbidden attributes | `scripts/legal_visibility.py` | `test_r4_visibility_attributes_guard` |
| M16 Legal class placement | `scripts/legal_visibility.py` | `test_r4_class_placement` |
| M17 privacy visibility wiring | `scripts/check_privacy_text.py` | `test_r4_privacy_visibility` |
| M18 footer visibility wiring | `scripts/check_invariants.py` | `test_r4_footer_visibility` |
| M19 D26 privacy statement destination | `scripts/check_privacy_text.py` | `test_r4_github_privacy_href` |
| M20 D26 ICO destination | `scripts/check_privacy_text.py` | `test_ico_href` |
| M21 title copy | `scripts/check_invariants.py` | `test_r4_banned_metadata` |
| M22 description copy | `scripts/check_invariants.py` | `test_r4_banned_metadata` |
| M23 og name copy | `scripts/check_invariants.py` | `test_r4_banned_metadata` |
| M24 twitter name copy | `scripts/check_invariants.py` | `test_r4_banned_metadata` |
| M25 og property copy | `scripts/check_invariants.py` | `test_r4_banned_metadata` |
| M26 twitter property copy | `scripts/check_invariants.py` | `test_r4_banned_metadata` |
| M27 alt copy | `scripts/check_invariants.py` | `test_r4_banned_metadata` |
| M28 title attribute copy | `scripts/check_invariants.py` | `test_r4_banned_metadata` |
| M29 aria-label copy | `scripts/check_invariants.py` | `test_r4_banned_metadata` |
| M30 XML processing instructions | `scripts/site_common.py` | `test_svg_xml_vectors` |
| M31 duplicate XML attributes ignoring case | `scripts/site_common.py` | `test_r4_svg_duplicate_attribute_case` |
| M32 resource checker markup errors | `scripts/check_no_third_party.py` | `test_r4_markup_all_checkers` |
| M33 link checker markup errors | `scripts/check_links.py` | `test_r4_markup_all_checkers` |
| M34 invariant checker markup errors | `scripts/check_invariants.py` | `test_r4_markup_all_checkers` |
| M35 privacy checker markup errors | `scripts/check_privacy_text.py` | `test_r4_markup_all_checkers` |
| M36 exact CODEOWNERS discovery exception | `scripts/site_common.py` | `test_r6_codeowners_discovery` |
| M37 exact .github file vocabulary | `scripts/site_common.py` | `test_r5_unknown_github_file` |
| M38 markup element allowlist | `scripts/allowlist.py` | `test_r5_unknown_element` |
| M39 markup attribute allowlist | `scripts/allowlist.py` | `test_r5_unknown_attribute` |
| M40 per-element attribute vocabulary | `scripts/allowlist.py` | `test_r5_all_forbidden_attributes` |
| M41 shared HTML vocabulary wiring | `scripts/site_common.py` | `test_r5_unknown_attribute` |
| M42 closing-tag vocabulary wiring | `scripts/site_common.py` | `test_r5_all_forbidden_elements` |
| M43 shared XML per-element vocabulary | `scripts/site_common.py` | `test_r5_svg_per_element_attributes` |
| M44 exact document rules wiring | `scripts/site_common.py` | `test_r5_csp_keyword` |
| M45 raw attribute byte comparison | `scripts/allowlist.py` | `test_r5_raw_attribute_bytes` |
| M46 exact html language | `scripts/allowlist.py` | `test_r5_html_lang` |
| M47 exact CSP keyword | `scripts/allowlist.py` | `test_r5_csp_keyword` |
| M48 exact CSP content in shared checks | `scripts/allowlist.py` | `test_r5_csp_content_shared` |
| M49 CSP cardinality in shared checks | `scripts/allowlist.py` | `test_r5_csp_count_shared` |
| M50 exact referrer value | `scripts/allowlist.py` | `test_r5_referrer_value` |
| M51 referrer cardinality | `scripts/allowlist.py` | `test_r5_referrer_count` |
| M52 exact link rel vocabulary | `scripts/allowlist.py` | `test_r5_link_rel` |
| M53 exact stylesheet target | `scripts/allowlist.py` | `test_r5_stylesheet_target` |
| M54 stylesheet cardinality on index | `scripts/allowlist.py` | `test_r5_extra_stylesheet_index` |
| M55 stylesheet cardinality on 404 | `scripts/allowlist.py` | `test_r5_extra_stylesheet_404` |
| M56 stylesheet required | `scripts/allowlist.py` | `test_r5_stylesheet_missing` |
| M57 exact favicon target | `scripts/allowlist.py` | `test_r5_icon_target` |
| M58 privacy check covers every document | `scripts/check_privacy_text.py` | `test_r5_extra_stylesheet_index` |
| M59 body background rejected by attribute vocabulary | `scripts/allowlist.py` | `test_r5_body_background` |
| M60 table background rejected by vocabulary | `scripts/allowlist.py` | `test_r5_table_background` |
| M61 initial exact doctype / BOM | `scripts/site_common.py` | `test_r6_doctype_byte_zero` |
| M62 all other declarations / comments | `scripts/site_common.py` | `test_r6_declarations` |
| M63 processing instructions | `scripts/site_common.py` | `test_r6_processing_instructions` |
| M64 control character range | `scripts/site_common.py` | `test_r6_controls` |
| M65 literal HTML reference set | `scripts/site_common.py` | `test_r6_references` |
| M66 nonvoid HTML slash | `scripts/site_common.py` | `test_r6_selfclosing_html` |
| M67 strict end-tag nesting | `scripts/site_common.py` | `test_r6_misnested_end` |
| M68 stray end tags | `scripts/site_common.py` | `test_r6_stray_end` |
| M69 explicit closure at EOF | `scripts/site_common.py` | `test_r6_unclosed` |
| M70 unique document root | `scripts/site_common.py` | `test_r6_document_root` |
| M71 head/body cardinality | `scripts/site_common.py` | `test_r6_head_body_cardinality` |
| M72 head then body order | `scripts/site_common.py` | `test_r6_head_body_order` |
| M73 direct head/body parents | `scripts/site_common.py` | `test_r6_head_body_parent` |
| M74 head element model | `scripts/site_common.py` | `test_r6_head_elements` |
| M75 structural whitespace only | `scripts/site_common.py` | `test_r6_structural_text` |
| M76 CSP before every link | `scripts/site_common.py` | `test_r6_csp_before_link` |
| M77 phrasing content models | `scripts/site_common.py` | `test_r6_phrasing_models` |
| M78 list child model | `scripts/site_common.py` | `test_r6_list_models` |
| M79 list text model | `scripts/site_common.py` | `test_r6_structural_text` |
| M80 li direct list parent | `scripts/site_common.py` | `test_r6_list_models` |
| M81 li flow vocabulary | `scripts/site_common.py` | `test_r6_li_flow` |
| M82 HTML flow model | `scripts/site_common.py` | `test_r6_flow_models` |
| M83 nested anchors | `scripts/site_common.py` | `test_r6_nested_anchor` |
| M84 title RCDATA | `scripts/site_common.py` | `test_r6_title_rcdata` |
| M85 SVG integration text only | `scripts/site_common.py` | `test_r6_svg_integration` |
| M86 double-quoted attributes | `scripts/site_common.py` | `test_r6_attributes_quoted` |
| M87 attribute whitespace separation | `scripts/site_common.py` | `test_r6_attribute_separation` |
| M88 no literal less-than in attributes | `scripts/site_common.py` | `test_r6_attribute_less_than` |
| M89 UTF-8 declaration and placement | `scripts/site_common.py` | `test_r6_charset` |
| M90 encoding sniff window | `scripts/site_common.py` | `test_r6_charset_sniff_window` |
| M91 malformed start token | `scripts/site_common.py` | `test_r6_malformed_tokens` |
| M92 malformed end token | `scripts/site_common.py` | `test_r6_malformed_tokens` |
| M93 malformed attribute token | `scripts/site_common.py` | `test_r6_malformed_tokens` |
| M94 browser whitespace insertion | `scripts/site_common.py` | `test_r6_document_whitespace` |
| M95 trailing whitespace placement | `scripts/site_common.py` | `test_r6_document_whitespace` |
| M96 invalid UTF-8 fails closed | `scripts/site_common.py` | `test_r6_utf8_bytes` |
| M97 li flow model | `scripts/site_common.py` | `test_r6_li_flow` |
| M98 addendum 2 font CSP | `scripts/allowlist.py` | `test_v4_old_p4_csp` |
| M99 exact font directory vocabulary | `scripts/site_common.py` | `test_v4_extra_font` |
| M100 font and licence hashes | `scripts/site_common.py` | `test_v4_font_hash` |
| M101 woff2 magic bytes | `scripts/site_common.py` | `test_v4_font_magic` |
| M102 CSS font origin and resource guard | `scripts/check_no_third_party.py` | `test_v4_font_face_origin` |
| M103 exact Legal bytes | `scripts/legal_pins.py` | `test_v4_legal_bytes` |
| M104 Legal element cardinality | `scripts/legal_pins.py` | `test_v4_second_legal_element` |
| M105 footer byte pin wiring | `scripts/check_invariants.py` | `test_v4_footer_svg` |
| M106 privacy byte pin wiring | `scripts/check_privacy_text.py` | `test_v4_notice_svg` |
| M107 approved footer semantics | `scripts/check_invariants.py` | `test_v4_pin_semantics` |
| M108 approved privacy D26 semantics | `scripts/check_privacy_text.py` | `test_v4_pin_semantics` |
| M109 missing footer pin | `scripts/check_invariants.py` | `test_v4_missing_pins` |
| M110 missing privacy pin | `scripts/check_privacy_text.py` | `test_v4_missing_pins` |
| M111 pin single exact fragment | `scripts/legal_pins.py` | `test_v4_pin_validation` |
| M112 pin strict subset validation | `scripts/legal_pins.py` | `test_v4_pin_validation` |
| M113 pin privacy vocabulary | `scripts/check_privacy_text.py` | `test_v4_pin_notice_vocabulary` |
| M114 pin privacy visibility | `scripts/check_privacy_text.py` | `test_v4_pin_notice_visibility` |
| M115 banned copy includes aria-hidden SVG | `scripts/site_common.py` | `test_v4_banned_aria_svg` |
| M116 pinned D26 link semantics | `scripts/check_privacy_text.py` | `test_v4_pin_notice_links` |
| M117 exact Legal discovery exceptions | `scripts/site_common.py` | `test_all_document_suffixes_and_no_exclusions` |
| M118 approved image bytes and presence | `scripts/site_common.py` | `test_logo_image_hashes` |
| M119 PNG signature | `scripts/site_common.py` | `test_logo_png_signature` |
| M120 pinned img src | `scripts/allowlist.py` | `test_logo_img_source` |
| M121 unknown image file | `scripts/site_common.py` | `test_logo_unknown_image` |
| M122 pinned icon and apple-touch-icon href | `scripts/allowlist.py` | `test_logo_icon_source` |
| M123 image attribute vocabulary | `scripts/allowlist.py` | `test_logo_img_attributes` |
| M124 privacy logo identity | `scripts/check_privacy_text.py` | `test_logo_privacy_brand` |
| M125 ICO signature | `scripts/site_common.py` | `test_favicon_ico_signature` |
| M126 exact three icon links | `scripts/allowlist.py` | `test_favicon_links_exact` |
| M127 icon links in head | `scripts/allowlist.py` | `test_favicon_links_head` |
| M128 retired image rejection | `scripts/site_common.py` | `test_favicon_retired_files` |
| M129 favicon.ico byte pin | `scripts/site_common.py` | `test_logo_image_hashes` |
| M130 coami-icon.svg byte pin | `scripts/site_common.py` | `test_logo_image_hashes` |
| M131 apple-touch-icon.png byte pin | `scripts/site_common.py` | `test_logo_image_hashes` |
| M132 manifest resource ban | `scripts/check_no_third_party.py` | `test_favicon_manifest` |
| M133 Features pin hash | `scripts/check_v5.py` | `test_v5_feature_pin` |
| M134 Features complete ordered copy | `scripts/check_v5.py` | `test_v5_feature_words` |
| M135 Features exactly once | `scripts/check_v5.py` | `test_v5_feature_words` |
| M136 Features item status association | `scripts/check_v5.py` | `test_v5_feature_status_association` |
| M137 Features exact status counts | `scripts/check_v5.py` | `test_v5_feature_status_counts` |
| M138 notice forbidden on other pages | `scripts/check_privacy_text.py` | `test_v5_notice_only_privacy` |
| M139 whole word claim ban | `scripts/check_v5.py` | `test_v5_claims_every_page` |
| M140 claims scan attributes | `scripts/check_v5.py` | `test_v5_claims_all_copy` |
| M141 Legal claim exemption | `scripts/check_v5.py` | `test_v5_claim_pin_exception` |
| M142 reduced motion coverage | `scripts/check_v5.py` | `test_v5_motion_remove_reduce` |
| M143 new keyframes require coverage | `scripts/check_v5.py` | `test_v5_motion_new_keyframe` |
| M144 override must follow animation | `scripts/check_v5.py` | `test_v5_motion_new_selector` |
| M145 transition coverage | `scripts/check_v5.py` | `test_v5_motion_transition` |
| M146 reduced motion media condition | `scripts/check_v5.py` | `test_v5_motion_wrong_condition` |
| M147 CSS parse fails closed | `scripts/check_v5.py` | `test_v5_motion_parse_fail_closed` |
| M148 infinite animation size | `scripts/check_v5.py` | `test_v5_motion_infinite` |
| M149 v5 CI enforcement wiring | `scripts/ci_checks.py` | `test_v5_ci_wiring` |
| M150 pinned footer band | `scripts/check_privacy_text.py` | `test_v5_footer_band` |
| M151 important animation cannot use universal override | `scripts/check_v5.py` | `test_v5_motion_important` |
| M152 live chat exception scope | `scripts/check_v5.py` | `test_r2_live_chat_outside_item` |
| M153 live chat requires pinned item | `scripts/check_v5.py` | `test_r2_live_chat_requires_pin` |
| M154 live chat requires trusted pin hash | `scripts/check_v5.py` | `test_r2_live_chat_pin_hash` |
| M155 exact live chat phrase | `scripts/check_v5.py` | `test_r2_go_live_in_item` |
| M156 purple CSS declaration scope | `scripts/check_v5.py` | `test_r2_purple_button` |
| M157 purple inline attribute scan | `scripts/check_v5.py` | `test_r2_purple_inline_svg` |
| M158 all purple selectors must be allowed | `scripts/check_v5.py` | `test_r2_purple_selector_scope` |
| M159 purple stylesheet scope | `scripts/check_v5.py` | `test_r2_purple_other_css` |
| M160 purple asset scope | `scripts/check_v5.py` | `test_r2_purple_inline_svg` |
| M161 purple hue guard | `scripts/check_v5.py` | `test_r2_purple_hue_guard` |
| M162 frozen purple RGB identity | `scripts/check_v5.py` | `test_r2_purple_palette_identity` |
| M163 purple CSS parse fails closed | `scripts/check_v5.py` | `test_r2_purple_parse_fail_closed` |
| M164 purple CI enforcement wiring | `scripts/check_v5.py` | `test_r2_purple_wiring` |
| M165 purple enso sibling exclusion | `scripts/check_v5.py` | `test_r2_purple_selector_scope` |
| M166 purple exact enso class | `scripts/check_v5.py` | `test_r2_purple_selector_scope` |
| M167 live remains banned in Legal text | `scripts/check_v5.py` | `test_r2_live_chat_legal_elements` |
| M168 live remains banned in Legal attributes | `scripts/check_v5.py` | `test_r2_live_chat_legal_elements` |
| M169 purple rule and at-rule preludes | `scripts/check_v5.py` | `test_r2_purple_rule_preludes` |
| M170 whole-page pin hash | `scripts/page_pins.py` | `test_r3_page_pin_integrity` |
| M171 whole-page skeleton comparison | `scripts/page_pins.py` | `test_r3_added_about_sentence` |
| M172 pin every page | `scripts/page_pins.py` | `test_r3_added_about_sentence` |
| M173 skeleton class lists | `scripts/page_pins.py` | `test_r3_skeleton_classes` |
| M174 skeleton attributes | `scripts/page_pins.py` | `test_r3_skeleton_attributes` |
| M175 exact direct text slots | `scripts/page_pins.py` | `test_r3_skeleton_text_slots` |
| M176 shared element boundaries | `scripts/site_common.py` | `test_r3_text_element_boundaries` |
| M177 parent inserts empty-element boundaries | `scripts/site_common.py` | `test_r3_text_element_boundaries` |
| M178 claims use separated scan | `scripts/check_v5.py` | `test_r3_added_actions_split_spans` |
| M179 pinned row uses separated text | `scripts/check_v5.py` | `test_r3_raw_text_pin_exception_boundaries` |
| M180 visibility pin placement exceptions | `scripts/page_visibility.py` | `test_r3_disclaimer_brand_dark` |
| M181 visibility skip placement | `scripts/page_visibility.py` | `test_r3_status_spans_skip` |
| M182 visibility display guard | `scripts/page_visibility.py` | `test_r3_visibility_display` |
| M183 visibility hidden guard | `scripts/page_visibility.py` | `test_r3_visibility_hidden` |
| M184 visibility opacity and font zero | `scripts/page_visibility.py` | `test_r3_visibility_opacity_font` |
| M185 visibility clipping | `scripts/page_visibility.py` | `test_r3_visibility_sr_only` |
| M186 visibility positioned offscreen | `scripts/page_visibility.py` | `test_r3_visibility_positioned` |
| M187 visibility text indentation | `scripts/page_visibility.py` | `test_r3_visibility_transform_indent` |
| M188 visibility translation | `scripts/page_visibility.py` | `test_r3_visibility_transform_indent` |
| M189 visibility collapsed height | `scripts/page_visibility.py` | `test_r3_visibility_collapsed` |
| M190 visibility split declaration aggregation | `scripts/page_visibility.py` | `test_r3_visibility_collapsed` |
| M191 visibility nonclass selectors | `scripts/page_visibility.py` | `test_r3_visibility_all_selectors` |
| M192 visibility media context | `scripts/page_visibility.py` | `test_r3_visibility_context_and_other_css` |
| M193 visibility all stylesheets | `scripts/page_visibility.py` | `test_r3_visibility_context_and_other_css` |
| M194 visibility exact rule exceptions | `scripts/page_visibility.py` | `test_r3_visibility_exception_rules_fixed` |
| M195 visibility trusted pins required | `scripts/page_visibility.py` | `test_r3_visibility_pin_required` |
| M196 visibility attributes | `scripts/page_visibility.py` | `test_r3_visibility_attributes` |
| M197 visibility parser fails closed | `scripts/page_visibility.py` | `test_r3_visibility_parse_fail_closed` |
| M198 page pins CI wiring | `scripts/check_v5.py` | `test_r3_pages_wiring` |
| M199 visibility CI wiring | `scripts/check_v5.py` | `test_r3_visibility_wiring` |
| M200 retain original joined-word ban | `scripts/check_invariants.py` | `test_r3_original_ban_split_words` |
| M201 duplicate resolved landmark name | `index.html` | `test_r4_landmark_names` |
| M202 audit reduced motion | `scripts/ci_checks.py` | `test_r4_a11y_reduced_motion_config` |
| M203 gradient on content-bearing hero | `style.css` | `test_r5_gradient_backgrounds_decorative` |
| M204 hero stacking isolation | `style.css` | `test_r5_hero_glow_stacking` |
| M205 glow behind hero content | `style.css` | `test_r5_hero_glow_stacking` |
| M206 decorative negative layer is not hiding | `scripts/page_visibility.py` | `test_r5_hero_glow_visibility` |
| M207 serve audit copy | `scripts/ci_checks.py` | `test_r6_a11y_copy` |
| M208 audit glow override | `scripts/ci_checks.py` | `test_r6_a11y_copy` |
| M209 candidate stays untouched | `scripts/ci_checks.py` | `test_r6_a11y_copy` |
| M210 peak alpha blend | `scripts/hero_contrast.py` | `test_r6_contrast_baseline` |
| M211 percent alpha scale | `scripts/hero_contrast.py` | `test_r6_contrast_math` |
| M212 contrast minimum | `scripts/hero_contrast.py` | `test_r6_stronger_glow` |
| M213 dark contrast enforcement | `scripts/hero_contrast.py` | `test_r6_stronger_glow` |
| M214 light contrast enforcement | `scripts/hero_contrast.py` | `test_r6_text_thresholds` |
| M215 normal text threshold | `scripts/hero_contrast.py` | `test_r6_text_thresholds` |
| M216 button text thresholds | `scripts/hero_contrast.py` | `test_r6_text_thresholds` |
| M217 outline threshold | `scripts/hero_contrast.py` | `test_r6_outline_threshold` |
| M218 colour parse fails closed | `scripts/hero_contrast.py` | `test_r6_unparsable_colours` |
| M219 missing tokens fail closed | `scripts/hero_contrast.py` | `test_r6_missing_and_scoped_tokens` |
| M220 decorative layer contract | `scripts/hero_contrast.py` | `test_r6_decorative_layer` |
| M221 text paint contract | `scripts/hero_contrast.py` | `test_r6_paint_contract` |
| M222 scoped token guard | `scripts/hero_contrast.py` | `test_r6_missing_and_scoped_tokens` |
| M223 duplicate token guard | `scripts/hero_contrast.py` | `test_r6_missing_and_scoped_tokens` |
| M224 colour channel ranges | `scripts/hero_contrast.py` | `test_r6_unparsable_colours` |
| M225 sRGB linearisation | `scripts/hero_contrast.py` | `test_r6_contrast_math` |
| M226 contrast CI wiring | `scripts/check_v5.py` | `test_r6_contrast_wiring` |
| M227 monotone gradient proof | `scripts/hero_contrast.py` | `test_r6_nonmonotone_glow` |

| M228 head pin hash | `scripts/page_pins.py` | `test_r7_head_pin_integrity` |
| M229 head pin comparison | `scripts/page_pins.py` | `test_r7_title_every_page` |
| M230 unique head title | `scripts/page_pins.py` | `test_r7_head_cardinality` |
| M231 unique head description | `scripts/page_pins.py` | `test_r7_head_cardinality` |
| M232 nonempty head title | `scripts/page_pins.py` | `test_r7_empty_head` |
| M233 nonempty head description | `scripts/page_pins.py` | `test_r7_empty_head` |
| M234 head meta allowlist | `scripts/page_pins.py` | `test_r7_head_meta_allowlist` |
| M235 head link allowlist | `scripts/page_pins.py` | `test_r7_head_link_allowlist` |
| M236 head enforcement wiring | `scripts/page_pins.py` | `test_r7_description_every_page` |
| M237 title pin value | `scripts/page_pins.py` | `test_r7_head_baseline` |
| M238 description pin value | `scripts/page_pins.py` | `test_r7_head_baseline` |
| M239 metadata joined-word ban | `scripts/check_invariants.py` | `test_r7_head_joined_ban` |
| M240 availability title scan | `scripts/check_v5.py` | `test_r7_head_availability_title` |
| M241 availability description scan | `scripts/check_v5.py` | `test_r7_head_availability_description` |
| M242 joined head availability scan | `scripts/check_v5.py` | `test_r7_head_joined_availability` |
| M243 live chat forbidden in head | `scripts/check_v5.py` | `test_r7_head_live_chat_scope` |
| M244 head pin generation | `scripts/generate_page_pins.py` | `test_r7_head_generator` |
| M245 banned description scan | `scripts/check_invariants.py` | `test_r7_head_banned_words` |
| M246 banned title scan | `scripts/check_invariants.py` | `test_r7_head_banned_words` |

| M247 separated head banned-word scan | `scripts/check_invariants.py` | `test_r7_head_separated_ban` |
| M248 separated head availability scan | `scripts/check_v5.py` | `test_r7_head_separated_availability` |
| M249 head generator fails closed | `scripts/generate_page_pins.py` | `test_r7_head_generator` |
| M250 authenticated footer baseline | `scripts/legal_pins.py` | `test_sol_coordinated_footer_tampering` |
| M251 authenticated privacy baseline | `scripts/legal_pins.py` | `test_sol_coordinated_privacy_tampering` |
| M252 hero colour selector guard | `scripts/hero_contrast.py` | `test_sol_hero_colour_selectors` |

Expected caught/total: **252/252**. Actual execution is saved in `../test.txt`.

M207–M227 cover the temporary audit copy, its exact stylesheet override and
candidate preservation, peak-alpha compositing, both theme thresholds, normal
text and button states, the non-text outline, closed colour parsing, token
scope/completeness, the decorative-layer and paint contracts, sRGB maths,
monotone gradient bounds and CI enforcement.


M228–M249 cover head pin integrity and exact values, unique and non-empty
titles/descriptions, the fixed meta/link allowlist, per-page enforcement,
metadata generation, both claim scanners and their joined-text scans, and the
restriction of live chat to approved Features body items.

M250–M252 cover coordinated byte-only edits to both Legal baselines and their
pages, and unguarded colour rules with tag, ancestor, universal, attribute,
functional-pseudo, grouped and button-state selectors, including at-rule scopes.
Semantic/parser Legal fixtures explicitly trust only their temporary test
digest, keeping those older guards independently mutation-tested after adding
baseline authentication. Production digests and Legal files remain fixed.
