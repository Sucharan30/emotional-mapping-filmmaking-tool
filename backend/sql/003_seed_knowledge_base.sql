-- =============================================================
-- 003_seed_knowledge_base.sql
-- Seed data for the knowledge base (~20 entries).
-- Run AFTER 001_foundation.sql.
--
-- IMPORTANT — READ BEFORE USING:
--   Every entry is marked review_status = 'draft'.
--   These are starting drafts based on general cinematographic
--   conventions. A researcher should review each entry against
--   empirical literature, correct any overstatements, and add
--   a source_note before changing status to 'reviewed'.
--
--   Emotional responses to camera technique depend on many
--   factors outside this data: performance, lighting, sound,
--   editing, story context, and individual viewer differences.
--   These entries describe tendencies, not guarantees.
--
-- Idempotent: ON CONFLICT (technique_name) DO NOTHING
-- =============================================================

INSERT INTO knowledge_base
    (technique_name, category, visual_characteristic,
     potential_emotions, context_note,
     example_scene, equipment_needs, typical_complexity,
     review_status)
VALUES

-- ── ANGLES ──────────────────────────────────────────────────

(
  'Low Angle',
  'angle',
  'Camera positioned below the subject eye level, pointing upward. Subject appears larger and often dominates the background.',
  ARRAY['power', 'tension', 'blame'],
  'Low-angle framing can contribute to a perception of dominance or threat in some viewers, but the effect depends heavily on performance, character context, lighting, and the story situation. The same framing can convey heroism in one scene and menace in another.',
  'A authority figure standing over a seated character; a villain making a speech to a crowd.',
  'Standard camera or tripod positioned at or near ground level. No specialised equipment required.',
  'Low',
  'draft'
),

(
  'High Angle',
  'angle',
  'Camera positioned above the subject eye level, pointing downward. Subject appears smaller within its environment.',
  ARRAY['vulnerability', 'isolation', 'empathy'],
  'High-angle framing may suggest diminishment or vulnerability in a character, though the same angle can also convey an omniscient observer perspective. The emotional read depends significantly on the character''s performance, the environment shown, and the surrounding edit.',
  'A lone figure in a vast empty space; a character overwhelmed by circumstances.',
  'Camera elevated above head height. Achievable with a raised tripod, C-stand arm, or elevated platform. A ladder may suffice indoors.',
  'Low',
  'draft'
),

(
  'Eye Level',
  'angle',
  'Camera positioned at approximately the subject''s eye level. Suggests equality or neutrality in the viewer relationship.',
  ARRAY['empathy', 'intimacy'],
  'Eye-level framing is generally perceived as neutral and relatable. It is widely used for dialogue scenes to foster audience identification, but its emotional effect relies primarily on performance and scene context rather than the angle itself.',
  'A conversation between two characters of equal standing; a character addressing the audience directly.',
  'Standard tripod or handheld at natural eye height. No specialised equipment.',
  'Low',
  'draft'
),

(
  'Dutch Angle',
  'angle',
  'Camera tilted on its roll axis so the horizon appears diagonal within the frame. Creates visual imbalance.',
  ARRAY['tension', 'detachment'],
  'The Dutch angle is strongly associated with unease or psychological instability in certain film traditions. Its effectiveness depends on degree of tilt and frequency of use — sustained or overused Dutch angles may read as stylistic affectation rather than emotional signal.',
  'A character experiencing disorientation or moral crisis; a psychological thriller confrontation.',
  'Standard tripod with an adjustable head, or handheld with a deliberate tilt. No specialised equipment beyond normal camera support.',
  'Low',
  'draft'
),

(
  'Overhead (Bird''s Eye)',
  'angle',
  'Camera placed directly above the subject and pointing straight down. Removes the viewer from ground-level human perspective.',
  ARRAY['isolation', 'detachment', 'vulnerability'],
  'Overhead framing can emphasise spatial relationships, patterns, or a character''s smallness relative to their environment. The emotional effect depends greatly on what the subject is doing, how they move, and what the accompanying sound conveys.',
  'A character lying on the floor after a crisis; a crowd seen from directly above.',
  'Overhead camera rig, tall C-stand arm, elevated platform, or drone (outdoors). Requires more planning and rigging than standard angles.',
  'Medium',
  'draft'
),

-- ── SHOT TYPES ──────────────────────────────────────────────

(
  'Extreme Close-Up',
  'shot_type',
  'Fills the frame with a very small area of the subject — typically eyes, mouth, or a telling detail. Removes spatial context entirely.',
  ARRAY['tension', 'intimacy', 'empathy'],
  'Extreme close-ups can intensify emotional focus by directing attention to a specific detail, but their effect depends on the quality of the detail chosen and the performance. An expressionless extreme close-up carries a very different weight than an emotionally charged one.',
  'Eyes reacting to shocking news; trembling hands; a significant object at a critical moment.',
  'Standard lens with good close-focus capability, or a macro lens. A monopod or tripod helps maintain stability at high magnification.',
  'Low',
  'draft'
),

(
  'Close-Up',
  'shot_type',
  'Frames the face from approximately chin to top of head. The character''s expression fills the screen.',
  ARRAY['empathy', 'intimacy'],
  'Close-ups are a primary tool for encouraging audience connection with a character''s inner state, but the emotional read depends entirely on what the performance communicates in that moment and how the edit contextualises it.',
  'A reaction shot during an emotional revelation; a character listening to difficult news.',
  'Standard camera and lens. Tripod or monopod recommended for stability. No specialised equipment.',
  'Low',
  'draft'
),

(
  'Medium Shot',
  'shot_type',
  'Frames the subject from approximately the waist upward. Shows both facial expression and upper body language.',
  ARRAY['empathy'],
  'The medium shot is a versatile, conversational framing that balances facial expression with body language. Often considered a neutral observational distance, it relies primarily on performance rather than framing for its emotional tone.',
  'Two characters in dialogue; a character performing an action while speaking.',
  'Standard camera and lens at conversational distance. Tripod or handheld. No specialised equipment.',
  'Low',
  'draft'
),

(
  'Wide Shot',
  'shot_type',
  'Shows the full subject body within a larger environment. Emphasises spatial context over facial expression.',
  ARRAY['isolation', 'detachment'],
  'Wide shots contextualise a character within their environment. They can suggest isolation when the character is small relative to the surroundings, or belonging when the environment is warm and populated. The emotional tone is heavily shaped by the environment itself and the character''s body language.',
  'A lone figure walking across a vast landscape; establishing a character''s relationship to their setting.',
  'Standard camera and a wider focal-length lens. No specialised equipment beyond normal camera support.',
  'Low',
  'draft'
),

(
  'Extreme Wide Shot',
  'distance',
  'Subject appears very small relative to the surrounding environment. Often used to establish geography or a character''s relationship to vast space.',
  ARRAY['isolation', 'vulnerability', 'detachment'],
  'Extreme wide shots minimise a character''s visible emotional expression in favour of spatial context. Their emotional effect is largely determined by the quality of the environment, the character''s position and movement within it, and accompanying sound design.',
  'A character crossing a desert; a figure standing at the edge of a cliff; a person lost in a city crowd.',
  'Standard camera with a wide-angle or zoom lens. Drone can achieve dramatic aerial versions.',
  'Low',
  'draft'
),

(
  'Two-Shot',
  'shot_type',
  'Frames two subjects in the same shot, typically showing their spatial relationship to one another.',
  ARRAY['empathy', 'tension', 'intimacy'],
  'Two-shots make the spatial and relational dynamic between characters visible simultaneously. The emotional read depends on proximity, facing direction, power balance within the frame, and what each character is doing.',
  'A confrontation between two characters; a moment of closeness between two people.',
  'Standard camera and lens. No specialised equipment.',
  'Low',
  'draft'
),

-- ── FRAMING ─────────────────────────────────────────────────

(
  'Over-the-Shoulder',
  'framing',
  'Camera placed behind one character''s shoulder, pointing toward another. Both characters appear in the frame, establishing their spatial relationship.',
  ARRAY['empathy', 'tension'],
  'Over-the-shoulder framing can align the audience loosely with one character''s perspective while keeping the other character visible. The emotional alignment depends on whose shoulder is shown, the eyeline, and how matching angles are used in editing.',
  'A dialogue exchange; an interview or interrogation scene.',
  'Standard camera and lens. Eyeline adjustments may be needed for significant height differences between subjects.',
  'Low',
  'draft'
),

(
  'Point of View (POV)',
  'framing',
  'Camera represents the subjective viewpoint of a specific character — what that character sees, from approximately where they see it.',
  ARRAY['empathy', 'tension', 'intimacy'],
  'POV shots can strongly identify the viewer with a specific character''s experience at that moment, but require clear editorial context (a preceding shot showing the character looking) to be read correctly. Overuse can become distancing or feel technique-forward rather than emotionally grounded.',
  'A character discovering something alarming; a character reaching toward someone.',
  'Handheld or a rig simulating eye-level motion. May use a stabiliser for controlled movement. Low setup complexity.',
  'Low',
  'draft'
),

-- ── MOVEMENT ────────────────────────────────────────────────

(
  'Static Camera',
  'movement',
  'Camera is fixed in position throughout the shot. No pan, tilt, or physical movement.',
  ARRAY['tension', 'isolation', 'detachment'],
  'A static camera can create a sense of observation, formality, or emotional restraint. It can heighten tension by refusing to follow action, or suggest detachment by keeping the frame fixed as events unfold. Effect depends heavily on duration and what happens within the frame.',
  'A long take of a character alone in a room; a fixed frame during a tense confrontation.',
  'Tripod only. No movement equipment needed.',
  'Low',
  'draft'
),

(
  'Handheld',
  'movement',
  'Camera is physically held by the operator, producing organic irregular movement that varies with operator breathing and body movement.',
  ARRAY['tension', 'empathy', 'intimacy'],
  'Handheld camera can suggest immediacy, documentary authenticity, or character agitation depending on the degree of movement and genre context. Subtle handheld may feel like a present, breathing observer; aggressive handheld may feel chaotic. Effect depends on what audiences have been conditioned to expect in the genre.',
  'A chase sequence; an intimate documentary-style character study; a scene of emotional volatility.',
  'Camera operated handheld or on a shoulder rig. No additional movement equipment needed.',
  'Low',
  'draft'
),

(
  'Slow Push-In',
  'movement',
  'Camera moves slowly toward the subject on a dolly, slider, or gimbal during the shot, gradually tightening the framing.',
  ARRAY['tension', 'intimacy', 'empathy'],
  'A slow push-in can build emotional intensity by progressively reducing environmental context and drawing the viewer closer to the subject. The effect depends on rate of movement, starting and ending frame sizes, and what the performance communicates during the move.',
  'A character receiving difficult news; the emotional climax of a conversation.',
  'Slider or dolly for smooth motion. A motorised slider or small dolly improves smoothness. Requires more setup and rehearsal than a static shot.',
  'Medium',
  'draft'
),

(
  'Tracking Shot (Follow)',
  'movement',
  'Camera moves parallel to or following the subject as they move through space, maintaining a relatively consistent relationship to the subject.',
  ARRAY['empathy', 'tension'],
  'Tracking shots can sustain audience engagement with a moving character and create shared momentum. The emotional effect depends on pace, direction of movement, and whether the character is moving toward something meaningful or away from it. Tracking shots require careful choreography between actor, camera operator, and focus puller.',
  'A character walking purposefully to a destination; a pursuit sequence.',
  'Dolly and track, or a motorised gimbal and a camera vehicle or dolly. Requires dedicated crew. A gimbal reduces crew size but changes the movement quality.',
  'High',
  'draft'
),

(
  'Pan',
  'movement',
  'Camera rotates horizontally around its vertical axis from a fixed position, following or revealing subjects across the frame.',
  ARRAY['detachment', 'isolation'],
  'Pans can reveal spatial relationships between subjects or connect two points in a scene. A slow deliberate pan across a space can feel surveying and detached; a fast whip pan creates energy and disorientation. Effect depends heavily on speed, what is revealed, and accompanying sound.',
  'Scanning a location to show its scale; transitioning between two characters in the same space; a reveal pan.',
  'Standard tripod with a fluid head capable of smooth horizontal rotation.',
  'Low',
  'draft'
),

(
  'Tilt',
  'movement',
  'Camera rotates vertically around its horizontal axis from a fixed position, typically revealing height from bottom to top or top to bottom.',
  ARRAY['power', 'vulnerability'],
  'Tilting upward along a figure can suggest scale or authority; tilting downward can reveal smallness or defeat. The effect depends on what the camera reveals and in what order, combined with the character''s performance.',
  'Revealing an imposing figure from feet upward; revealing a character''s defeated posture from above.',
  'Standard tripod with a fluid head capable of smooth vertical rotation.',
  'Low',
  'draft'
),

(
  'Zoom',
  'movement',
  'Optical zoom changes focal length during the shot, altering the angle of view and perspective compression without physically moving the camera.',
  ARRAY['tension', 'detachment'],
  'A zoom-in differs perceptually from a dolly push-in despite arriving at a similar frame size: it changes perspective compression and can feel more analytical or distancing than a physical camera move. Rapid zooms carry genre associations. Slow zooms are relatively rare in contemporary practice and may read as deliberate or stylised depending on context.',
  'Slowly zooming in on a distant detail the character cannot reach; a stylised genre beat.',
  'A lens with a zoom range (or two primes at different focal lengths in editing). No movement equipment needed.',
  'Low',
  'draft'
)

ON CONFLICT (technique_name) DO NOTHING;
