/**
 * StreamPlayerPage - Video player với hệ thống phụ đề linh hoạt
 * 
 * Features:
 * - HTML5 video player với Range request (206 Partial Content)
 * - Hỗ trợ 2 track phụ đề đồng thời (Track 1 + Track 2)
 * - Mỗi track có thể là: sub từ server HOẶC file VTT/SRT do người dùng tải lên
 * - Tự động convert SRT → VTT
 * - Dịch phụ đề sang ngôn ngữ khác bằng Gemini API
 * - Hiển thị song ngữ (Track 1 dưới, Track 2 trên)
 * - Transcript panel hiển thị cả 2 track
 */
import { useState, useRef, useEffect, useCallback, useMemo } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { mediaStreamApi, type MediaSubtitle } from '@/api/mediastream';
import { Button } from '@/components/ui/Button';
import { Select } from '@/components/ui/Select';
import { SEO } from '@/components/common';
import Spinner, { LoadingInline } from '@/components/ui/Spinner';
import {
  Play,
  Pause,
  Volume2,
  VolumeX,
  Maximize,
  ArrowLeft,
  Languages,
  Eye,
  Clock,
  BarChart2,
  Globe,
  FileText,
  ChevronUp,
  ChevronDown,
  Upload,
  X,
} from 'lucide-react';
import GeminiApiKeyManager, { getStoredGeminiApiKey } from '@/components/stream/GeminiApiKeyManager';

// ============================================================================
// Subtitle Parsing (VTT + SRT)
// ============================================================================

interface SubtitleCue {
  index: number;
  startTime: number; // seconds
  endTime: number;
  text: string;
}

/**
 * Parse timestamp → seconds
 * Supports: HH:MM:SS.mmm, HH:MM:SS,mmm (SRT), MM:SS.mmm
 */
function parseTimestamp(ts: string): number {
  // SRT uses comma: 00:01:23,456 → replace with dot
  ts = ts.replace(',', '.').trim();
  const parts = ts.split(':');
  if (parts.length === 3) {
    return parseInt(parts[0]) * 3600 + parseInt(parts[1]) * 60 + parseFloat(parts[2]);
  } else if (parts.length === 2) {
    return parseInt(parts[0]) * 60 + parseFloat(parts[1]);
  }
  return 0;
}

/**
 * Detect if content is SRT format (not VTT)
 */
function isSRT(content: string): boolean {
  const trimmed = content.trim();
  return !trimmed.startsWith('WEBVTT') && /^\d+\s*\n/.test(trimmed);
}

/**
 * Convert SRT content to VTT format
 */
function srtToVtt(srtContent: string): string {
  let vtt = 'WEBVTT\n\n';
  const converted = srtContent
    .replace(/\r\n/g, '\n')
    .replace(/(\d{2}:\d{2}:\d{2}),(\d{3})/g, '$1.$2');
  vtt += converted;
  return vtt;
}

/**
 * Parse VTT/SRT content into SubtitleCue[]
 */
function parseSubtitleContent(content: string): SubtitleCue[] {
  const vttContent = isSRT(content) ? srtToVtt(content) : content;
  const cues: SubtitleCue[] = [];
  const lines = vttContent.trim().split('\n');
  let i = 0;

  // Skip WEBVTT header and any metadata
  while (i < lines.length && !lines[i].includes('-->')) {
    i++;
  }

  let cueIndex = 0;
  while (i < lines.length) {
    const line = lines[i].trim();

    if (line.includes('-->')) {
      const [startStr, endStr] = line.split('-->').map(s => s.trim());
      const startTime = parseTimestamp(startStr);
      const endTime = parseTimestamp(endStr);

      const textLines: string[] = [];
      i++;
      while (i < lines.length && lines[i].trim() !== '' && !lines[i].includes('-->')) {
        const trimmedLine = lines[i].trim();
        if (!trimmedLine.match(/^\d+$/)) {
          textLines.push(trimmedLine.replace(/<[^>]+>/g, ''));
        }
        i++;
      }

      if (textLines.length > 0) {
        cues.push({
          index: cueIndex++,
          startTime,
          endTime,
          text: textLines.join(' '),
        });
      }
    } else {
      i++;
    }
  }

  return cues;
}

function formatTime(seconds: number): string {
  const h = Math.floor(seconds / 3600);
  const m = Math.floor((seconds % 3600) / 60);
  const s = Math.floor(seconds % 60);
  if (h > 0) return `${h}:${m.toString().padStart(2, '0')}:${s.toString().padStart(2, '0')}`;
  return `${m}:${s.toString().padStart(2, '0')}`;
}

// ============================================================================
// Subtitle Track Source Types
// ============================================================================

type TrackSource =
  | { type: 'none' }
  | { type: 'server'; subtitleId: number; label: string }
  | { type: 'file'; fileName: string; content: string }
  | { type: 'translate'; targetLang: string; label: string };

const TRANSLATE_LANGUAGES = [
  { value: 'vi', label: '🇻🇳 Tiếng Việt' },
  { value: 'en', label: '🇬🇧 English' },
  { value: 'de', label: '🇩🇪 Deutsch' },
  { value: 'fr', label: '🇫🇷 Français' },
  { value: 'ja', label: '🇯🇵 日本語' },
  { value: 'ko', label: '🇰🇷 한국어' },
  { value: 'zh', label: '🇨🇳 中文' },
];

// ============================================================================
// SubtitleTrackControl Component
// ============================================================================

interface TrackControlProps {
  trackNumber: 1 | 2;
  label: string;
  colorClasses: string;
  serverSubtitles: MediaSubtitle[];
  source: TrackSource;
  onSourceChange: (source: TrackSource) => void;
  isLoading?: boolean;
}

function SubtitleTrackControl({
  trackNumber,
  label,
  colorClasses,
  serverSubtitles,
  source,
  onSourceChange,
  isLoading,
}: TrackControlProps) {
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [activeTab, setActiveTab] = useState<'server' | 'file' | 'translate'>(
    source.type === 'file' ? 'file' : source.type === 'translate' ? 'translate' : 'server'
  );

  const handleFileUpload = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    const reader = new FileReader();
    reader.onload = () => {
      const content = reader.result as string;
      onSourceChange({ type: 'file', fileName: file.name, content });
    };
    reader.readAsText(file);
    e.target.value = '';
  }, [onSourceChange]);

  const handleClear = useCallback(() => {
    onSourceChange({ type: 'none' });
    setActiveTab('server');
  }, [onSourceChange]);

  return (
    <div className={`border-2 rounded-lg p-3 ${colorClasses}`}>
      <div className="flex items-center justify-between mb-2">
        <span className="text-xs font-bold uppercase tracking-wide text-vintage-dark/70">
          {label}
        </span>
        {source.type !== 'none' && (
          <button
            onClick={handleClear}
            className="text-vintage-tan hover:text-red-500 transition"
            title="Tắt track"
          >
            <X className="h-3.5 w-3.5" />
          </button>
        )}
      </div>

      {/* Tab buttons */}
      <div className="flex gap-1 mb-2">
        <button
          onClick={() => setActiveTab('server')}
          className={`text-xs px-2 py-1 rounded-md transition font-medium ${
            activeTab === 'server'
              ? 'bg-vintage-olive text-white'
              : 'bg-vintage-tan/10 text-vintage-dark/60 hover:bg-vintage-tan/20'
          }`}
        >
          <Globe className="h-3 w-3 inline mr-1" />
          Server
        </button>
        <button
          onClick={() => setActiveTab('file')}
          className={`text-xs px-2 py-1 rounded-md transition font-medium ${
            activeTab === 'file'
              ? 'bg-vintage-olive text-white'
              : 'bg-vintage-tan/10 text-vintage-dark/60 hover:bg-vintage-tan/20'
          }`}
        >
          <Upload className="h-3 w-3 inline mr-1" />
          File
        </button>
        <button
          onClick={() => setActiveTab('translate')}
          className={`text-xs px-2 py-1 rounded-md transition font-medium ${
            activeTab === 'translate'
              ? 'bg-vintage-olive text-white'
              : 'bg-vintage-tan/10 text-vintage-dark/60 hover:bg-vintage-tan/20'
          }`}
        >
          <Languages className="h-3 w-3 inline mr-1" />
          Dịch AI
        </button>
      </div>

      {/* Tab content */}
      {activeTab === 'server' && (
        <Select
          value={source.type === 'server' ? String(source.subtitleId) : ''}
          onChange={(e) => {
            const val = e.target.value;
            if (val) {
              const sub = serverSubtitles.find(s => s.id === parseInt(val));
              onSourceChange({
                type: 'server',
                subtitleId: parseInt(val),
                label: sub?.label || sub?.language || val,
              });
            } else {
              onSourceChange({ type: 'none' });
            }
          }}
          options={[
            { value: '', label: '— Chọn phụ đề —' },
            ...serverSubtitles.map(s => ({
              value: String(s.id),
              label: s.label || s.language,
            })),
          ]}
        />
      )}

      {activeTab === 'file' && (
        <div>
          <input
            ref={fileInputRef}
            type="file"
            accept=".vtt,.srt"
            onChange={handleFileUpload}
            className="hidden"
          />
          {source.type === 'file' ? (
            <div className="flex items-center gap-2 bg-vintage-cream/50 rounded-lg px-3 py-2">
              <FileText className="h-4 w-4 text-vintage-olive flex-shrink-0" />
              <span className="text-sm text-vintage-dark truncate flex-1">{source.fileName}</span>
              <button
                onClick={() => fileInputRef.current?.click()}
                className="text-xs text-vintage-olive hover:underline flex-shrink-0"
              >
                Đổi
              </button>
            </div>
          ) : (
            <button
              onClick={() => fileInputRef.current?.click()}
              className="w-full flex items-center justify-center gap-2 border-2 border-dashed border-vintage-tan/40 rounded-lg px-3 py-3 text-sm text-vintage-tan hover:border-vintage-olive hover:text-vintage-olive transition"
            >
              <Upload className="h-4 w-4" />
              Tải file .VTT hoặc .SRT
            </button>
          )}
        </div>
      )}

      {activeTab === 'translate' && (
        <div className="flex items-center gap-2">
          <Select
            value={source.type === 'translate' ? source.targetLang : ''}
            onChange={(e) => {
              const lang = e.target.value;
              if (lang) {
                const langItem = TRANSLATE_LANGUAGES.find(l => l.value === lang);
                onSourceChange({
                  type: 'translate',
                  targetLang: lang,
                  label: langItem?.label || lang,
                });
              } else {
                onSourceChange({ type: 'none' });
              }
            }}
            options={[
              { value: '', label: '— Chọn ngôn ngữ —' },
              ...TRANSLATE_LANGUAGES,
            ]}
          />
          {isLoading && <LoadingInline />}
        </div>
      )}

      {/* Current status */}
      {source.type !== 'none' && (
        <div className="mt-1.5 text-xs text-vintage-olive font-medium truncate">
          {source.type === 'server' && `✓ ${source.label}`}
          {source.type === 'file' && `✓ ${source.fileName}`}
          {source.type === 'translate' && (isLoading ? '⏳ Đang dịch...' : `✓ Dịch: ${source.label}`)}
        </div>
      )}
    </div>
  );
}

// ============================================================================
// Main Component
// ============================================================================

export default function StreamPlayerPage() {
  const { uid } = useParams<{ uid: string }>();
  const navigate = useNavigate();

  // Video ref
  const videoRef = useRef<HTMLVideoElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);

  // Player state
  const [isPlaying, setIsPlaying] = useState(false);
  const [currentTime, setCurrentTime] = useState(0);
  const [duration, setDuration] = useState(0);
  const [isMuted, setIsMuted] = useState(false);
  const [showTranscript, setShowTranscript] = useState(false);

  // Dual subtitle tracks
  const [track1Source, setTrack1Source] = useState<TrackSource>({ type: 'none' });
  const [track2Source, setTrack2Source] = useState<TrackSource>({ type: 'none' });
  const [track1Cues, setTrack1Cues] = useState<SubtitleCue[]>([]);
  const [track2Cues, setTrack2Cues] = useState<SubtitleCue[]>([]);
  const [isTranslating1, setIsTranslating1] = useState(false);
  const [isTranslating2, setIsTranslating2] = useState(false);
  const [translateError, setTranslateError] = useState('');
  const [geminiApiKey, setGeminiApiKey] = useState(() => getStoredGeminiApiKey());

  // Fetch media data
  const { data: media, isLoading, error } = useQuery({
    queryKey: ['stream-media', uid],
    queryFn: () => mediaStreamApi.getByUid(uid!),
    enabled: !!uid,
  });

  // ========================================================================
  // Load Track Cues
  // ========================================================================

  const loadServerSubtitle = useCallback(async (subtitleId: number): Promise<SubtitleCue[]> => {
    const subtitle = media?.subtitles?.find((s: MediaSubtitle) => s.id === subtitleId);
    if (!subtitle) return [];
    try {
      const content = await mediaStreamApi.getSubtitleContent(subtitle.subtitle_url);
      return parseSubtitleContent(content);
    } catch (err) {
      console.error('Failed to load subtitle:', err);
      return [];
    }
  }, [media]);

  // Reference subtitle ID for translation (Track 1 server > Track 2 server > first available)
  const getReferenceSubtitleId = useCallback((): number | null => {
    if (track1Source.type === 'server') return track1Source.subtitleId;
    if (track2Source.type === 'server') return track2Source.subtitleId;
    if (media?.subtitles?.length) return media.subtitles[0].id;
    return null;
  }, [track1Source, track2Source, media]);

  // Load Track 1 cues
  useEffect(() => {
    let cancelled = false;

    const load = async () => {
      if (track1Source.type === 'none') {
        setTrack1Cues([]);
        return;
      }
      if (track1Source.type === 'server') {
        const cues = await loadServerSubtitle(track1Source.subtitleId);
        if (!cancelled) setTrack1Cues(cues);
      }
      if (track1Source.type === 'file') {
        const cues = parseSubtitleContent(track1Source.content);
        if (!cancelled) setTrack1Cues(cues);
      }
      if (track1Source.type === 'translate') {
        const refId = getReferenceSubtitleId();
        if (!refId) return;
        setIsTranslating1(true);
        try {
          const data = await mediaStreamApi.translateSubtitle({
            subtitle_id: refId,
            target_lang: track1Source.targetLang,
            ...(geminiApiKey ? { gemini_api_key: geminiApiKey } : {}),
          });
          if (!cancelled) {
            setTrack1Cues(parseSubtitleContent(data.translated_vtt));
            setTranslateError('');
          }
        } catch (err: any) {
          if (!cancelled) {
            setTranslateError(err?.response?.data?.error || err.message || 'Translation failed');
          }
        } finally {
          if (!cancelled) setIsTranslating1(false);
        }
      }
    };

    load();
    return () => { cancelled = true; };
  }, [track1Source, loadServerSubtitle, getReferenceSubtitleId, geminiApiKey]);

  // Load Track 2 cues
  useEffect(() => {
    let cancelled = false;

    const load = async () => {
      if (track2Source.type === 'none') {
        setTrack2Cues([]);
        return;
      }
      if (track2Source.type === 'server') {
        const cues = await loadServerSubtitle(track2Source.subtitleId);
        if (!cancelled) setTrack2Cues(cues);
      }
      if (track2Source.type === 'file') {
        const cues = parseSubtitleContent(track2Source.content);
        if (!cancelled) setTrack2Cues(cues);
      }
      if (track2Source.type === 'translate') {
        const refId = getReferenceSubtitleId();
        if (!refId) return;
        setIsTranslating2(true);
        try {
          const data = await mediaStreamApi.translateSubtitle({
            subtitle_id: refId,
            target_lang: track2Source.targetLang,
            ...(geminiApiKey ? { gemini_api_key: geminiApiKey } : {}),
          });
          if (!cancelled) {
            setTrack2Cues(parseSubtitleContent(data.translated_vtt));
            setTranslateError('');
          }
        } catch (err: any) {
          if (!cancelled) {
            setTranslateError(err?.response?.data?.error || err.message || 'Translation failed');
          }
        } finally {
          if (!cancelled) setIsTranslating2(false);
        }
      }
    };

    load();
    return () => { cancelled = true; };
  }, [track2Source, loadServerSubtitle, getReferenceSubtitleId, geminiApiKey]);

  // Auto-select default subtitle for Track 1
  useEffect(() => {
    if (media?.subtitles?.length && track1Source.type === 'none') {
      const defaultSub = media.subtitles.find((s: MediaSubtitle) => s.is_default);
      const sub = defaultSub || media.subtitles[0];
      setTrack1Source({
        type: 'server',
        subtitleId: sub.id,
        label: sub.label || sub.language,
      });
    }
  }, [media]);

  // ========================================================================
  // Active cues (based on currentTime)
  // ========================================================================

  const activeCue1 = useMemo(() => {
    return track1Cues.find(c => currentTime >= c.startTime && currentTime <= c.endTime) || null;
  }, [currentTime, track1Cues]);

  const activeCue2 = useMemo(() => {
    return track2Cues.find(c => currentTime >= c.startTime && currentTime <= c.endTime) || null;
  }, [currentTime, track2Cues]);

  // Transcript: primary = Track 1, secondary = Track 2
  const transcriptCues = track1Cues.length > 0 ? track1Cues : track2Cues;
  const secondaryCues = track1Cues.length > 0 && track2Cues.length > 0 ? track2Cues : [];

  // ========================================================================
  // Video event handlers
  // ========================================================================

  const handleTimeUpdate = useCallback(() => {
    if (videoRef.current) setCurrentTime(videoRef.current.currentTime);
  }, []);

  const handleLoadedMetadata = useCallback(() => {
    if (videoRef.current) setDuration(videoRef.current.duration);
  }, []);

  const togglePlay = useCallback(() => {
    if (!videoRef.current) return;
    if (videoRef.current.paused) {
      videoRef.current.play();
      setIsPlaying(true);
    } else {
      videoRef.current.pause();
      setIsPlaying(false);
    }
  }, []);

  const toggleMute = useCallback(() => {
    if (!videoRef.current) return;
    videoRef.current.muted = !videoRef.current.muted;
    setIsMuted(videoRef.current.muted);
  }, []);

  const handleSeek = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    if (!videoRef.current) return;
    const time = parseFloat(e.target.value);
    videoRef.current.currentTime = time;
    setCurrentTime(time);
  }, []);

  const toggleFullscreen = useCallback(() => {
    if (!containerRef.current) return;
    if (document.fullscreenElement) {
      document.exitFullscreen();
    } else {
      containerRef.current.requestFullscreen();
    }
  }, []);

  const seekToCue = useCallback((cue: SubtitleCue) => {
    if (!videoRef.current) return;
    videoRef.current.currentTime = cue.startTime;
    setCurrentTime(cue.startTime);
    if (videoRef.current.paused) {
      videoRef.current.play();
      setIsPlaying(true);
    }
  }, []);

  // ========================================================================
  // Loading / Error states
  // ========================================================================

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <Spinner size="lg" />
      </div>
    );
  }

  if (error || !media) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <Play className="h-16 w-16 text-vintage-tan/50 mx-auto mb-4" />
          <h2 className="text-xl font-serif font-bold text-vintage-dark mb-2">
            Video không tồn tại
          </h2>
          <Button onClick={() => navigate('/stream')} variant="outline">
            <ArrowLeft className="h-4 w-4 mr-2" />
            Quay lại
          </Button>
        </div>
      </div>
    );
  }

  const serverSubs = media.subtitles || [];

  // ========================================================================
  // Render
  // ========================================================================

  return (
    <>
      <SEO
        title={`${media.title} - Stream - UnstressVN`}
        description={media.description?.slice(0, 160) || media.title}
        type="website"
      />

      <div className="min-h-screen bg-vintage-light py-4 md:py-6">
        <div className="container-responsive">
          <div className="flex flex-col lg:flex-row gap-6">

            {/* === LEFT: Video Player + Controls === */}
            <div className="lg:w-2/3">

              {/* Video Container */}
              <div
                ref={containerRef}
                className="relative bg-black rounded-xl overflow-hidden shadow-2xl group"
              >
                {/* Video Element */}
                <video
                  ref={videoRef}
                  className="w-full aspect-video bg-black cursor-pointer"
                  poster={media.thumbnail_url || undefined}
                  onTimeUpdate={handleTimeUpdate}
                  onLoadedMetadata={handleLoadedMetadata}
                  onPlay={() => setIsPlaying(true)}
                  onPause={() => setIsPlaying(false)}
                  onClick={togglePlay}
                  preload="metadata"
                  playsInline
                >
                  <source src={media.stream_url} type={media.mime_type || 'video/mp4'} />
                  Trình duyệt không hỗ trợ video.
                </video>

                {/* ===== Subtitle Overlay ===== */}
                {(activeCue1 || activeCue2) && (
                  <div className="absolute bottom-16 left-0 right-0 flex flex-col items-center px-4 pointer-events-none gap-1">
                    {/* Track 2 (secondary - top, blue) */}
                    {activeCue2 && (
                      <div className="bg-black/70 text-blue-300 text-sm md:text-base px-4 py-1 rounded-lg text-center max-w-[90%] backdrop-blur-sm">
                        {activeCue2.text}
                      </div>
                    )}
                    {/* Track 1 (primary - bottom, white) */}
                    {activeCue1 && (
                      <div className="bg-black/80 text-white text-base md:text-lg px-4 py-1.5 rounded-lg text-center max-w-[90%] backdrop-blur-sm font-medium">
                        {activeCue1.text}
                      </div>
                    )}
                  </div>
                )}

                {/* Custom Controls Overlay */}
                <div className="absolute bottom-0 left-0 right-0 bg-gradient-to-t from-black/80 to-transparent p-3 opacity-0 group-hover:opacity-100 transition-opacity duration-300">
                  {/* Progress Bar */}
                  <input
                    type="range"
                    min={0}
                    max={duration || 0}
                    value={currentTime}
                    onChange={handleSeek}
                    step={0.1}
                    className="w-full h-1.5 bg-white/30 rounded-full appearance-none cursor-pointer
                      [&::-webkit-slider-thumb]:appearance-none [&::-webkit-slider-thumb]:w-3.5 [&::-webkit-slider-thumb]:h-3.5 [&::-webkit-slider-thumb]:rounded-full [&::-webkit-slider-thumb]:bg-vintage-olive [&::-webkit-slider-thumb]:cursor-pointer
                      [&::-moz-range-thumb]:w-3.5 [&::-moz-range-thumb]:h-3.5 [&::-moz-range-thumb]:rounded-full [&::-moz-range-thumb]:bg-vintage-olive [&::-moz-range-thumb]:cursor-pointer [&::-moz-range-thumb]:border-0"
                  />

                  {/* Controls Row */}
                  <div className="flex items-center justify-between mt-2">
                    <div className="flex items-center gap-3">
                      <button onClick={togglePlay} className="text-white hover:text-vintage-olive transition">
                        {isPlaying ? <Pause className="h-5 w-5" /> : <Play className="h-5 w-5" />}
                      </button>
                      <button onClick={toggleMute} className="text-white hover:text-vintage-olive transition">
                        {isMuted ? <VolumeX className="h-5 w-5" /> : <Volume2 className="h-5 w-5" />}
                      </button>
                      <span className="text-white text-xs font-mono">
                        {formatTime(currentTime)} / {formatTime(duration)}
                      </span>
                    </div>
                    <button onClick={toggleFullscreen} className="text-white hover:text-vintage-olive transition">
                      <Maximize className="h-5 w-5" />
                    </button>
                  </div>
                </div>
              </div>

              {/* ===== Subtitle Track Controls ===== */}
              <div className="mt-4 bg-white rounded-xl border-2 border-vintage-tan/30 p-4">
                <h3 className="text-sm font-bold text-vintage-dark mb-3 flex items-center gap-2">
                  <FileText className="h-4 w-4 text-vintage-olive" />
                  Phụ đề — Chọn nguồn cho mỗi track
                </h3>

                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                  {/* Track 1 */}
                  <SubtitleTrackControl
                    trackNumber={1}
                    label="Track 1 (chính)"
                    colorClasses="border-vintage-olive/30 bg-vintage-olive/5"
                    serverSubtitles={serverSubs}
                    source={track1Source}
                    onSourceChange={setTrack1Source}
                    isLoading={isTranslating1}
                  />

                  {/* Track 2 */}
                  <SubtitleTrackControl
                    trackNumber={2}
                    label="Track 2 (phụ)"
                    colorClasses="border-blue-300/30 bg-blue-50/50"
                    serverSubtitles={serverSubs}
                    source={track2Source}
                    onSourceChange={setTrack2Source}
                    isLoading={isTranslating2}
                  />
                </div>

                {translateError && (
                  <p className="text-xs text-red-500 mt-2">{translateError}</p>
                )}

                {/* Gemini API Key Manager */}
                <div className="mt-3">
                  <GeminiApiKeyManager
                    onKeyChange={(key) => setGeminiApiKey(key)}
                  />
                </div>
              </div>

              {/* ===== Video Info ===== */}
              <div className="mt-4 bg-white rounded-xl border-2 border-vintage-tan/30 p-6">
                <h1 className="text-2xl font-serif font-bold text-vintage-dark mb-3">
                  {media.title}
                </h1>

                <div className="flex flex-wrap items-center gap-4 text-sm text-vintage-tan mb-4 pb-4 border-b border-vintage-tan/20">
                  <span className="flex items-center gap-1">
                    <Eye className="h-4 w-4" />
                    {media.view_count} lượt xem
                  </span>
                  {media.duration_formatted && (
                    <span className="flex items-center gap-1">
                      <Clock className="h-4 w-4" />
                      {media.duration_formatted}
                    </span>
                  )}
                </div>

                <div className="flex flex-wrap gap-2 mb-4">
                  {media.language && (
                    <span className="inline-flex items-center px-3 py-1 rounded-full text-xs font-bold uppercase tracking-wide bg-vintage-olive/10 text-vintage-olive border border-vintage-olive/20">
                      <Globe className="h-3 w-3 mr-1" />
                      {media.language === 'vi' ? 'Tiếng Việt' : media.language === 'en' ? 'English' : media.language === 'de' ? 'Deutsch' : media.language}
                    </span>
                  )}
                  {media.level && media.level !== 'all' && (
                    <span className="inline-flex items-center px-3 py-1 rounded-full text-xs font-bold uppercase tracking-wide bg-vintage-blue/10 text-vintage-blue border border-vintage-blue/20">
                      <BarChart2 className="h-3 w-3 mr-1" />
                      {media.level}
                    </span>
                  )}
                </div>

                {media.description && (
                  <p className="text-vintage-dark/80 font-serif leading-relaxed whitespace-pre-wrap">
                    {media.description}
                  </p>
                )}

                <div className="flex flex-wrap gap-3 mt-6 pt-4 border-t border-vintage-tan/20">
                  <Button onClick={() => navigate('/stream')} variant="outline" className="border-vintage-tan text-vintage-dark hover:bg-vintage-cream">
                    <ArrowLeft className="h-4 w-4 mr-2" />
                    Quay lại
                  </Button>
                </div>
              </div>
            </div>

            {/* === RIGHT: Transcript Panel === */}
            <div className="lg:w-1/3">
              <div className="bg-white rounded-xl border-2 border-vintage-tan/30 overflow-hidden sticky top-4">
                {/* Transcript Header */}
                <button
                  onClick={() => setShowTranscript(!showTranscript)}
                  className="w-full flex items-center justify-between p-4 bg-vintage-cream/50 hover:bg-vintage-cream transition border-b border-vintage-tan/20"
                >
                  <div className="flex items-center gap-2">
                    <FileText className="h-5 w-5 text-vintage-olive" />
                    <span className="font-serif font-bold text-vintage-dark">
                      Transcript ({transcriptCues.length} câu)
                    </span>
                  </div>
                  {showTranscript ? (
                    <ChevronUp className="h-5 w-5 text-vintage-tan" />
                  ) : (
                    <ChevronDown className="h-5 w-5 text-vintage-tan" />
                  )}
                </button>

                {/* Transcript Content */}
                {showTranscript && (
                  <div className="max-h-[60vh] overflow-y-auto">
                    {transcriptCues.length === 0 ? (
                      <div className="p-6 text-center text-vintage-tan">
                        <FileText className="h-8 w-8 mx-auto mb-2 opacity-50" />
                        <p className="text-sm">Chọn phụ đề hoặc tải file sub để xem transcript</p>
                      </div>
                    ) : (
                      <div className="divide-y divide-vintage-tan/10">
                        {transcriptCues.map((cue) => {
                          const isActive = (activeCue1?.index === cue.index && track1Cues === transcriptCues)
                            || (activeCue2?.index === cue.index && track2Cues === transcriptCues);
                          const secondCue = secondaryCues.find(
                            sc => Math.abs(sc.startTime - cue.startTime) < 2
                          );

                          return (
                            <button
                              key={cue.index}
                              onClick={() => seekToCue(cue)}
                              className={`w-full text-left p-3 hover:bg-vintage-cream/50 transition ${
                                isActive ? 'bg-vintage-olive/10 border-l-4 border-vintage-olive' : ''
                              }`}
                            >
                              <div className="flex items-start gap-2">
                                <span className="text-xs font-mono text-vintage-tan whitespace-nowrap mt-0.5">
                                  {formatTime(cue.startTime)}
                                </span>
                                <div className="flex-1 min-w-0">
                                  <p className={`text-sm leading-relaxed ${
                                    isActive ? 'text-vintage-dark font-semibold' : 'text-vintage-dark/80'
                                  }`}>
                                    {cue.text}
                                  </p>
                                  {secondCue && (
                                    <p className="text-xs text-blue-600 mt-1 leading-relaxed">
                                      {secondCue.text}
                                    </p>
                                  )}
                                </div>
                              </div>
                            </button>
                          );
                        })}
                      </div>
                    )}
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      </div>
    </>
  );
}
