/**
 * StreamUploadPage — Smart Upload: Video + Subtitle → AI phân tích → tạo StreamMedia
 * Hỗ trợ: upload lên server (local) hoặc Google Drive (Service Account)
 * Chỉ admin/staff mới truy cập được.
 */
import { useState, useCallback, useRef, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '@/contexts/AuthContext';
import { Card, CardContent } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { Select } from '@/components/ui/Select';
import { SEO } from '@/components/common';
import GeminiApiKeyManager, { getStoredGeminiApiKey } from '@/components/stream/GeminiApiKeyManager';
import axios from 'axios';
import {
  Upload,
  FileVideo,
  FileText,
  Sparkles,
  FolderOpen,
  Tag,
  AlertCircle,
  CheckCircle,
  Loader2,
  ExternalLink,
  Trash2,
  Eye,
  HardDrive,
  Cloud,
  Settings,
  RefreshCw,
  ChevronDown,
  ChevronRight,
  Wifi,
  WifiOff,
  Shield,
} from 'lucide-react';

const LANGUAGES = [
  { value: '', label: 'Tự nhận diện' },
  { value: 'de', label: '🇩🇪 Tiếng Đức' },
  { value: 'en', label: '🇬🇧 Tiếng Anh' },
  { value: 'vi', label: '🇻🇳 Tiếng Việt' },
  { value: 'all', label: '🌐 Đa ngôn ngữ' },
];

const LEVELS = [
  { value: '', label: 'AI đề xuất' },
  { value: 'A1', label: 'A1 - Sơ cấp' },
  { value: 'A2', label: 'A2 - Cơ bản' },
  { value: 'B1', label: 'B1 - Trung cấp' },
  { value: 'B2', label: 'B2 - Trung cao' },
  { value: 'C1', label: 'C1 - Cao cấp' },
  { value: 'C2', label: 'C2 - Thành thạo' },
  { value: 'all', label: 'Tất cả trình độ' },
];

const MEDIA_TYPES = [
  { value: 'video', label: '🎬 Video' },
  { value: 'audio', label: '🎵 Audio' },
];

interface AIAnalysis {
  title: string;
  description: string;
  tags: string;
  level: string;
  key_phrases: string[];
  language_detected: string;
}

interface GDriveStatus {
  configured: boolean;
  email: string;
  folder_id: string;
  folder_name: string;
  folder_accessible: boolean;
  error: string | null;
}

interface GDriveFolder {
  id: string;
  name: string;
}

const api = axios.create({
  baseURL: '/media-stream',
  timeout: 300000,
});

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token && config.headers) {
    config.headers.Authorization = `Token ${token}`;
  }
  return config;
});

export default function StreamUploadPage() {
  const { user } = useAuth();
  const navigate = useNavigate();

  // File state
  const [videoFile, setVideoFile] = useState<File | null>(null);
  const [subtitleFile, setSubtitleFile] = useState<File | null>(null);
  const [gdriveUrl, setGdriveUrl] = useState('');
  const videoInputRef = useRef<HTMLInputElement>(null);
  const subInputRef = useRef<HTMLInputElement>(null);

  // Metadata state
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [tags, setTags] = useState('');
  const [language, setLanguage] = useState('');
  const [level, setLevel] = useState('');
  const [mediaType, setMediaType] = useState('video');
  const [subtitleLang, setSubtitleLang] = useState('');

  // AI analysis state
  const [aiAnalysis, setAiAnalysis] = useState<AIAnalysis | null>(null);
  const [analyzing, setAnalyzing] = useState(false);
  const [aiPowered, setAiPowered] = useState(false);

  // Upload state
  const [uploading, setUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [result, setResult] = useState<Record<string, unknown> | null>(null);
  const [error, setError] = useState('');

  // Upload destination: 'local' | 'gdrive'
  const [uploadDest, setUploadDest] = useState<'local' | 'gdrive'>('local');

  // Settings panel
  const [showSettings, setShowSettings] = useState(false);

  // Server key statuses
  const [serverKeyStatus, setServerKeyStatus] = useState<{ configured: boolean; key_prefix?: string } | null>(null);
  const [gdriveStatus, setGdriveStatus] = useState<GDriveStatus | null>(null);
  const [gdriveStatusLoading, setGdriveStatusLoading] = useState(false);

  // GDrive folder picker
  const [gdriveFolders, setGdriveFolders] = useState<GDriveFolder[]>([]);
  const [selectedFolder, setSelectedFolder] = useState('');

  // --- Load statuses on mount ---
  const checkServerKey = useCallback(async () => {
    try {
      const res = await api.get('/api/gemini-key-status/');
      setServerKeyStatus(res.data);
    } catch {
      setServerKeyStatus({ configured: false });
    }
  }, []);

  const checkGdriveStatus = useCallback(async () => {
    setGdriveStatusLoading(true);
    try {
      const res = await api.get('/api/gdrive-status/');
      setGdriveStatus(res.data);
      if (res.data.configured && res.data.folder_id) {
        setSelectedFolder(res.data.folder_id);
        if (res.data.folder_accessible) {
          setUploadDest('gdrive');
        }
      }
    } catch {
      setGdriveStatus(null);
    } finally {
      setGdriveStatusLoading(false);
    }
  }, []);

  const loadFolders = useCallback(async (parentId?: string) => {
    try {
      const params = parentId ? { parent: parentId } : {};
      const res = await api.get('/api/gdrive-folders/', { params });
      setGdriveFolders(res.data.folders || []);
    } catch {
      setGdriveFolders([]);
    }
  }, []);

  useEffect(() => {
    checkServerKey();
    checkGdriveStatus();
  }, [checkServerKey, checkGdriveStatus]);

  useEffect(() => {
    if (gdriveStatus?.configured && gdriveStatus?.folder_accessible) {
      loadFolders(gdriveStatus.folder_id || undefined);
    }
  }, [gdriveStatus, loadFolders]);

  // Access control
  if (!user?.is_staff && !user?.is_superuser) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <Card className="p-8 text-center max-w-md">
          <AlertCircle className="h-12 w-12 text-vintage-brown mx-auto mb-4" />
          <h2 className="text-xl font-bold mb-2">Không có quyền truy cập</h2>
          <p className="text-vintage-dark/60">Chỉ admin mới có thể upload video.</p>
        </Card>
      </div>
    );
  }

  // --- Analyze subtitle ---
  const handleAnalyze = async () => {
    if (!subtitleFile) return;
    setAnalyzing(true);
    setError('');
    const formData = new FormData();
    formData.append('subtitle', subtitleFile);
    const geminiKey = getStoredGeminiApiKey();
    if (geminiKey) formData.append('gemini_api_key', geminiKey);

    try {
      const res = await api.post('/analyze-subtitle/', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });
      const data = res.data;
      if (data.success && data.analysis) {
        setAiAnalysis(data.analysis);
        setAiPowered(data.ai_powered);
        if (!title) setTitle(data.analysis.title || '');
        if (!description) setDescription(data.analysis.description || '');
        if (!tags) setTags(data.analysis.tags || '');
        if (!level && data.analysis.level) setLevel(data.analysis.level);
        if (!language && data.analysis.language_detected) setLanguage(data.analysis.language_detected);
        if (!subtitleLang && data.analysis.language_detected) setSubtitleLang(data.analysis.language_detected);
      }
    } catch (err: unknown) {
      const msg = axios.isAxiosError(err) ? err.response?.data?.error : 'Lỗi phân tích phụ đề';
      setError(String(msg));
    } finally {
      setAnalyzing(false);
    }
  };

  // --- Upload ---
  const handleUpload = async () => {
    if (!videoFile && !gdriveUrl) {
      setError('Cần chọn video file hoặc nhập Google Drive URL');
      return;
    }
    if (!title.trim()) {
      setError('Vui lòng nhập tiêu đề');
      return;
    }
    setUploading(true);
    setError('');
    setUploadProgress(0);

    const formData = new FormData();
    if (videoFile) formData.append('video', videoFile);
    if (gdriveUrl) formData.append('gdrive_url', gdriveUrl);
    if (subtitleFile) formData.append('subtitle', subtitleFile);
    formData.append('title', title);
    formData.append('description', description);
    formData.append('tags', tags);
    formData.append('media_type', mediaType);
    if (language) formData.append('language', language);
    if (level) formData.append('level', level);
    if (subtitleLang) formData.append('subtitle_lang', subtitleLang);

    if (uploadDest === 'gdrive' && videoFile) {
      formData.append('upload_to_gdrive', 'true');
      if (selectedFolder) formData.append('gdrive_folder_id', selectedFolder);
    }

    const geminiKey = getStoredGeminiApiKey();
    if (geminiKey) formData.append('gemini_api_key', geminiKey);

    try {
      const res = await api.post('/smart-upload/', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
        onUploadProgress: (e) => {
          if (e.total) setUploadProgress(Math.round((e.loaded / e.total) * 100));
        },
      });
      setResult(res.data);
    } catch (err: unknown) {
      const msg = axios.isAxiosError(err) ? err.response?.data?.error : 'Lỗi upload';
      setError(String(msg));
    } finally {
      setUploading(false);
    }
  };

  // --- File handlers ---
  const handleVideoSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      setVideoFile(file);
      setGdriveUrl('');
      if (!title) {
        const name = file.name.replace(/\.[^.]+$/, '').replace(/[-_]/g, ' ');
        setTitle(name.charAt(0).toUpperCase() + name.slice(1));
      }
    }
  };

  const handleSubtitleSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) setSubtitleFile(file);
  };

  // --- Success view ---
  if (result) {
    const media = (result as { media?: { uid?: string; title?: string } }).media;
    return (
      <div className="max-w-2xl mx-auto py-8 px-4">
        <SEO title="Upload thành công" />
        <Card className="border-2 border-green-300 bg-green-50/30">
          <CardContent className="p-6 text-center space-y-4">
            <CheckCircle className="h-16 w-16 text-green-600 mx-auto" />
            <h2 className="text-2xl font-bold text-vintage-dark">Upload thành công!</h2>
            <p className="text-vintage-dark/70">{media?.title}</p>
            <div className="flex flex-wrap gap-2 justify-center">
              {(result as { ai_powered?: boolean }).ai_powered && (
                <span className="inline-flex items-center gap-1 px-3 py-1 rounded-full bg-purple-100 text-purple-700 text-sm">
                  <Sparkles className="h-3.5 w-3.5" /> AI phân tích
                </span>
              )}
              {(result as { uploaded_to_gdrive?: boolean }).uploaded_to_gdrive && (
                <span className="inline-flex items-center gap-1 px-3 py-1 rounded-full bg-blue-100 text-blue-700 text-sm">
                  <Cloud className="h-3.5 w-3.5" /> Google Drive
                </span>
              )}
            </div>
            <div className="flex gap-3 justify-center pt-4">
              <Button onClick={() => navigate(`/stream/${media?.uid}`)}>
                <Eye className="h-4 w-4 mr-1" /> Xem video
              </Button>
              <Button variant="outline" onClick={() => {
                setResult(null); setVideoFile(null); setSubtitleFile(null);
                setTitle(''); setDescription(''); setTags('');
                setAiAnalysis(null); setUploadProgress(0);
              }}>
                <Upload className="h-4 w-4 mr-1" /> Upload tiếp
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto py-6 px-4 space-y-6">
      <SEO title="Smart Upload Video" />

      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-vintage-dark flex items-center gap-2">
            <Upload className="h-6 w-6 text-vintage-olive" />
            Smart Upload Video
          </h1>
          <p className="text-sm text-vintage-dark/60 mt-1">
            Upload video + phụ đề → AI tự động phân tích nội dung, tạo tiêu đề & mô tả
          </p>
        </div>
        <Button variant="ghost" size="sm" onClick={() => setShowSettings(!showSettings)}>
          <Settings className="h-4 w-4 mr-1" />
          Cấu hình
        </Button>
      </div>

      {/* Connection Status Badges */}
      <div className="flex flex-wrap gap-2">
        <StatusBadge label="Gemini AI" configured={!!serverKeyStatus?.configured} loading={!serverKeyStatus} />
        <StatusBadge
          label="Google Drive"
          configured={!!gdriveStatus?.configured}
          loading={gdriveStatusLoading}
          detail={gdriveStatus?.email ? gdriveStatus.email.split('@')[0] : undefined}
        />
        {gdriveStatus?.configured && (
          <StatusBadge
            label={`Folder: ${gdriveStatus?.folder_name || gdriveStatus?.folder_id || 'Root'}`}
            configured={!!gdriveStatus?.folder_accessible}
            loading={false}
          />
        )}
      </div>

      {/* Settings Panel */}
      {showSettings && (
        <Card className="border-vintage-tan/30">
          <CardContent className="p-4 space-y-4">
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <h3 className="text-sm font-bold flex items-center gap-1.5">
                  <Sparkles className="h-4 w-4 text-purple-500" />
                  Gemini AI — Phân tích phụ đề
                </h3>
                {serverKeyStatus?.configured && (
                  <span className="text-xs text-green-600 flex items-center gap-1">
                    <CheckCircle className="h-3 w-3" /> Server key: {serverKeyStatus.key_prefix}
                  </span>
                )}
              </div>
              <GeminiApiKeyManager compact />
              <SaveServerKeySection onSaved={checkServerKey} />
            </div>
            <hr className="border-vintage-tan/20" />
            <GDriveCredentialsPanel status={gdriveStatus} onStatusChange={checkGdriveStatus} />
          </CardContent>
        </Card>
      )}

      {/* Error */}
      {error && (
        <div className="p-3 rounded-lg bg-red-50 border border-red-200 text-red-700 text-sm flex items-start gap-2">
          <AlertCircle className="h-4 w-4 mt-0.5 shrink-0" />
          {error}
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Left: Files */}
        <div className="space-y-4">
          {/* Upload Destination */}
          {gdriveStatus?.configured && (
            <Card>
              <CardContent className="p-3">
                <p className="text-xs font-bold text-vintage-dark/70 mb-2">Lưu trữ video tại:</p>
                <div className="flex gap-2">
                  <button
                    onClick={() => setUploadDest('local')}
                    className={`flex-1 flex items-center gap-2 px-3 py-2 rounded-lg border-2 text-sm transition-colors ${
                      uploadDest === 'local'
                        ? 'border-vintage-olive bg-vintage-olive/5 text-vintage-olive font-bold'
                        : 'border-vintage-tan/30 text-vintage-dark/60 hover:border-vintage-tan/50'
                    }`}
                  >
                    <HardDrive className="h-4 w-4" />
                    <div className="text-left">
                      <div>Server (Local)</div>
                      <div className="text-[10px] opacity-70">Lưu trên VPS</div>
                    </div>
                  </button>
                  <button
                    onClick={() => setUploadDest('gdrive')}
                    className={`flex-1 flex items-center gap-2 px-3 py-2 rounded-lg border-2 text-sm transition-colors ${
                      uploadDest === 'gdrive'
                        ? 'border-blue-500 bg-blue-50 text-blue-700 font-bold'
                        : 'border-vintage-tan/30 text-vintage-dark/60 hover:border-vintage-tan/50'
                    }`}
                  >
                    <Cloud className="h-4 w-4" />
                    <div className="text-left">
                      <div>Google Drive</div>
                      <div className="text-[10px] opacity-70">Upload → GDrive</div>
                    </div>
                  </button>
                </div>
                {uploadDest === 'gdrive' && gdriveFolders.length > 0 && (
                  <div className="mt-2">
                    <Select
                      options={[
                        { value: gdriveStatus?.folder_id || '', label: `📂 ${gdriveStatus?.folder_name || 'Mặc định'}` },
                        ...gdriveFolders.map(f => ({ value: f.id, label: `📁 ${f.name}` })),
                      ]}
                      value={selectedFolder}
                      onChange={(e) => setSelectedFolder(e.target.value)}
                    />
                  </div>
                )}
              </CardContent>
            </Card>
          )}

          {/* Video File */}
          <Card>
            <CardContent className="p-4 space-y-3">
              <h3 className="text-sm font-bold flex items-center gap-1.5">
                <FileVideo className="h-4 w-4 text-vintage-olive" />
                Video
              </h3>
              <div
                className={`border-2 border-dashed rounded-lg p-4 text-center cursor-pointer transition-colors
                  ${videoFile ? 'border-green-300 bg-green-50/30' : 'border-vintage-tan/40 hover:border-vintage-olive/40'}`}
                onClick={() => videoInputRef.current?.click()}
              >
                <input ref={videoInputRef} type="file" accept="video/*,audio/*" className="hidden" onChange={handleVideoSelect} />
                {videoFile ? (
                  <div className="flex items-center justify-between">
                    <div className="text-left">
                      <p className="text-sm font-medium truncate max-w-[200px]">{videoFile.name}</p>
                      <p className="text-xs text-vintage-dark/50">{(videoFile.size / (1024 * 1024)).toFixed(1)} MB</p>
                    </div>
                    <Button variant="ghost" size="sm" onClick={(e) => { e.stopPropagation(); setVideoFile(null); }}>
                      <Trash2 className="h-4 w-4" />
                    </Button>
                  </div>
                ) : (
                  <>
                    <FileVideo className="h-8 w-8 text-vintage-dark/30 mx-auto mb-2" />
                    <p className="text-sm text-vintage-dark/50">Chọn file video/audio</p>
                    <p className="text-xs text-vintage-dark/30">MP4, WebM, MP3, M4A...</p>
                  </>
                )}
              </div>
              {uploadDest === 'local' && (
                <>
                  <div className="relative">
                    <div className="absolute inset-x-0 top-1/2 border-t border-vintage-tan/30" />
                    <p className="relative text-center"><span className="bg-white px-3 text-xs text-vintage-dark/40">hoặc</span></p>
                  </div>
                  <div className="flex gap-2">
                    <div className="flex-1">
                      <Input
                        placeholder="Google Drive URL (https://drive.google.com/...)"
                        value={gdriveUrl}
                        onChange={(e) => { setGdriveUrl(e.target.value); if (e.target.value) setVideoFile(null); }}
                      />
                    </div>
                    <a href="https://drive.google.com" target="_blank" rel="noopener noreferrer" className="inline-flex items-center px-2 text-vintage-olive hover:text-vintage-brown">
                      <ExternalLink className="h-4 w-4" />
                    </a>
                  </div>
                </>
              )}
            </CardContent>
          </Card>

          {/* Subtitle File */}
          <Card>
            <CardContent className="p-4 space-y-3">
              <h3 className="text-sm font-bold flex items-center gap-1.5">
                <FileText className="h-4 w-4 text-vintage-blue" />
                Phụ đề (subtitle)
              </h3>
              <div
                className={`border-2 border-dashed rounded-lg p-4 text-center cursor-pointer transition-colors
                  ${subtitleFile ? 'border-blue-300 bg-blue-50/30' : 'border-vintage-tan/40 hover:border-vintage-blue/40'}`}
                onClick={() => subInputRef.current?.click()}
              >
                <input ref={subInputRef} type="file" accept=".vtt,.srt" className="hidden" onChange={handleSubtitleSelect} />
                {subtitleFile ? (
                  <div className="flex items-center justify-between">
                    <div className="text-left">
                      <p className="text-sm font-medium truncate max-w-[200px]">{subtitleFile.name}</p>
                      <p className="text-xs text-vintage-dark/50">{(subtitleFile.size / 1024).toFixed(1)} KB</p>
                    </div>
                    <Button variant="ghost" size="sm" onClick={(e) => { e.stopPropagation(); setSubtitleFile(null); setAiAnalysis(null); }}>
                      <Trash2 className="h-4 w-4" />
                    </Button>
                  </div>
                ) : (
                  <>
                    <FileText className="h-8 w-8 text-vintage-dark/30 mx-auto mb-2" />
                    <p className="text-sm text-vintage-dark/50">Chọn file phụ đề (.vtt / .srt)</p>
                    <p className="text-xs text-vintage-dark/30">AI sẽ phân tích để tạo tiêu đề & mô tả</p>
                  </>
                )}
              </div>
              {subtitleFile && (
                <div className="flex gap-2">
                  <Select
                    options={[
                      { value: '', label: 'Tự nhận diện' },
                      { value: 'de', label: '🇩🇪 Đức' },
                      { value: 'en', label: '🇬🇧 Anh' },
                      { value: 'vi', label: '🇻🇳 Việt' },
                    ]}
                    value={subtitleLang}
                    onChange={(e) => setSubtitleLang(e.target.value)}
                    className="flex-1"
                  />
                  <Button onClick={handleAnalyze} disabled={analyzing} className="shrink-0">
                    {analyzing ? <Loader2 className="h-4 w-4 animate-spin mr-1" /> : <Sparkles className="h-4 w-4 mr-1" />}
                    {analyzing ? 'Đang phân tích...' : 'AI Phân tích'}
                  </Button>
                </div>
              )}
              {aiAnalysis && (
                <div className="rounded-lg border border-purple-200 bg-purple-50/30 p-3 space-y-2">
                  <div className="flex items-center gap-1.5 text-sm font-bold text-purple-700">
                    <Sparkles className="h-3.5 w-3.5" />
                    {aiPowered ? 'Gemini AI phân tích' : 'Phân tích cơ bản'}
                  </div>
                  {aiAnalysis.key_phrases?.length > 0 && (
                    <div>
                      <p className="text-xs text-purple-600/70 mb-1">Cụm từ nổi bật:</p>
                      <div className="flex flex-wrap gap-1">
                        {aiAnalysis.key_phrases.map((phrase, i) => (
                          <span key={i} className="px-2 py-0.5 rounded-full bg-purple-100 text-purple-700 text-xs">{phrase}</span>
                        ))}
                      </div>
                    </div>
                  )}
                  <p className="text-xs text-purple-600/70">
                    Ngôn ngữ: <strong>{aiAnalysis.language_detected}</strong> | Trình độ: <strong>{aiAnalysis.level}</strong>
                  </p>
                </div>
              )}
            </CardContent>
          </Card>
        </div>

        {/* Right: Metadata */}
        <div className="space-y-4">
          <Card>
            <CardContent className="p-4 space-y-3">
              <h3 className="text-sm font-bold flex items-center gap-1.5">
                <Tag className="h-4 w-4 text-vintage-olive" />
                Thông tin video
              </h3>
              <Input label="Tiêu đề *" placeholder="Tiêu đề video (bắt buộc)" value={title} onChange={(e) => setTitle(e.target.value)} />
              <div>
                <label className="block text-sm font-medium mb-1">Mô tả</label>
                <textarea
                  className="w-full rounded-lg border border-vintage-tan/40 px-3 py-2 text-sm min-h-[80px] resize-y focus:outline-none focus:ring-2 focus:ring-vintage-olive/30 focus:border-vintage-olive"
                  placeholder="Mô tả nội dung video..."
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                />
              </div>
              <Input label="Tags" placeholder="Từ khóa, phân cách bằng dấu phẩy" value={tags} onChange={(e) => setTags(e.target.value)} />
              <div className="grid grid-cols-3 gap-2">
                <Select label="Loại" options={MEDIA_TYPES} value={mediaType} onChange={(e) => setMediaType(e.target.value)} />
                <Select label="Ngôn ngữ" options={LANGUAGES} value={language} onChange={(e) => setLanguage(e.target.value)} />
                <Select label="Trình độ" options={LEVELS} value={level} onChange={(e) => setLevel(e.target.value)} />
              </div>
            </CardContent>
          </Card>

          {/* Upload Button */}
          <Button
            className="w-full h-12 text-base"
            onClick={handleUpload}
            disabled={uploading || (!videoFile && !gdriveUrl)}
          >
            {uploading ? (
              <>
                <Loader2 className="h-5 w-5 animate-spin mr-2" />
                {uploadDest === 'gdrive' && videoFile ? 'Đang upload → GDrive...' : 'Đang upload...'} {uploadProgress}%
              </>
            ) : (
              <>
                {uploadDest === 'gdrive' && videoFile ? <Cloud className="h-5 w-5 mr-2" /> : <Upload className="h-5 w-5 mr-2" />}
                {uploadDest === 'gdrive' && videoFile ? 'Upload → Google Drive' : 'Upload Video'}
              </>
            )}
          </Button>
          {uploading && (
            <div className="w-full bg-vintage-tan/20 rounded-full h-2">
              <div className="bg-vintage-olive h-2 rounded-full transition-all duration-300" style={{ width: `${uploadProgress}%` }} />
            </div>
          )}
        </div>
      </div>
    </div>
  );
}


// ============================================================================
// Status Badge
// ============================================================================
function StatusBadge({ label, configured, loading, detail }: {
  label: string; configured: boolean; loading: boolean; detail?: string;
}) {
  if (loading) {
    return (
      <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-gray-100 text-gray-500 text-xs">
        <Loader2 className="h-3 w-3 animate-spin" /> {label}
      </span>
    );
  }
  return (
    <span className={`inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs ${
      configured ? 'bg-green-50 text-green-700 border border-green-200' : 'bg-red-50 text-red-600 border border-red-200'
    }`}>
      {configured ? <Wifi className="h-3 w-3" /> : <WifiOff className="h-3 w-3" />}
      {label}
      {detail && <span className="opacity-60">({detail})</span>}
    </span>
  );
}


// ============================================================================
// GDrive Credentials Panel
// ============================================================================
function GDriveCredentialsPanel({ status, onStatusChange }: {
  status: GDriveStatus | null;
  onStatusChange: () => void;
}) {
  const [expanded, setExpanded] = useState(false);
  const [jsonInput, setJsonInput] = useState('');
  const [folderIdInput, setFolderIdInput] = useState('');
  const [saving, setSaving] = useState(false);
  const [testing, setTesting] = useState(false);
  const [message, setMessage] = useState('');
  const [testResult, setTestResult] = useState<{ connected: boolean; email: string; error: string | null } | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleFileUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onload = (ev) => {
      const content = ev.target?.result as string;
      setJsonInput(content);
      try {
        const parsed = JSON.parse(content);
        if (parsed.type === 'service_account' && parsed.client_email) {
          setMessage(`✅ JSON hợp lệ: ${parsed.client_email}`);
        } else {
          setMessage('⚠️ Không phải Service Account JSON');
        }
      } catch {
        setMessage('❌ File không phải JSON hợp lệ');
      }
    };
    reader.readAsText(file);
  };

  const handleTest = async () => {
    if (!jsonInput.trim()) return;
    setTesting(true);
    setTestResult(null);
    setMessage('');
    try {
      const token = localStorage.getItem('token');
      const res = await axios.post('/media-stream/api/gdrive-check/', {
        service_account_json: jsonInput.trim(),
      }, {
        headers: { 'Content-Type': 'application/json', ...(token ? { Authorization: `Token ${token}` } : {}) },
      });
      setTestResult(res.data);
      if (res.data.connected) {
        setMessage(`✅ Kết nối thành công — ${res.data.email}`);
      } else {
        setMessage(`❌ ${res.data.error}`);
      }
    } catch (err: unknown) {
      const msg = axios.isAxiosError(err) ? err.response?.data?.error : 'Lỗi test kết nối';
      setMessage(`❌ ${msg}`);
    } finally {
      setTesting(false);
    }
  };

  const handleSave = async () => {
    if (!jsonInput.trim()) return;
    setSaving(true);
    setMessage('');
    try {
      const token = localStorage.getItem('token');
      const res = await axios.post('/media-stream/api/gdrive-credentials/', {
        service_account_json: jsonInput.trim(),
        folder_id: folderIdInput.trim(),
      }, {
        headers: { 'Content-Type': 'application/json', ...(token ? { Authorization: `Token ${token}` } : {}) },
      });
      setMessage(`✅ ${res.data.message} — ${res.data.email}`);
      setJsonInput('');
      setFolderIdInput('');
      onStatusChange();
    } catch (err: unknown) {
      const msg = axios.isAxiosError(err) ? err.response?.data?.error : 'Lỗi lưu credentials';
      setMessage(`❌ ${msg}`);
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-bold flex items-center gap-1.5">
          <Cloud className="h-4 w-4 text-blue-500" />
          Google Drive — Upload video
        </h3>
        <div className="flex items-center gap-2">
          {status?.configured ? (
            <span className="text-xs text-green-600 flex items-center gap-1">
              <CheckCircle className="h-3 w-3" /> {status.email.split('@')[0]}
            </span>
          ) : (
            <span className="text-xs text-amber-600 flex items-center gap-1">
              <AlertCircle className="h-3 w-3" /> Chưa cấu hình
            </span>
          )}
          <button onClick={() => setExpanded(!expanded)} className="p-1 rounded hover:bg-vintage-tan/10">
            {expanded ? <ChevronDown className="h-4 w-4" /> : <ChevronRight className="h-4 w-4" />}
          </button>
        </div>
      </div>

      {status?.configured && !expanded && (
        <div className="text-xs text-vintage-dark/60 space-y-0.5">
          <p>📧 Email: <span className="font-mono">{status.email}</span></p>
          {status.folder_name && <p>📂 Folder: <span className="font-medium">{status.folder_name}</span></p>}
          {status.folder_id && !status.folder_accessible && (
            <p className="text-amber-600">⚠️ Folder không truy cập được — hãy share folder với Service Account email</p>
          )}
        </div>
      )}

      {expanded && (
        <div className="space-y-3 bg-blue-50/30 rounded-lg p-3 border border-blue-100">
          <div className="text-xs text-vintage-dark/70 space-y-1">
            <p className="font-bold">Hướng dẫn cấu hình:</p>
            <ol className="list-decimal list-inside space-y-0.5 text-vintage-dark/60">
              <li>Vào <a href="https://console.cloud.google.com/iam-admin/serviceaccounts" target="_blank" rel="noopener noreferrer" className="text-blue-600 underline">Google Cloud Console → Service Accounts</a></li>
              <li>Tạo Service Account → tải file JSON key</li>
              <li>Bật <strong>Google Drive API</strong> trong project</li>
              <li>Share folder Google Drive với email của Service Account (quyền Editor)</li>
            </ol>
          </div>

          <div>
            <label className="block text-xs font-medium mb-1">Service Account JSON *</label>
            <div className="flex gap-2 mb-1">
              <input ref={fileInputRef} type="file" accept=".json" className="hidden" onChange={handleFileUpload} />
              <Button size="sm" variant="outline" onClick={() => fileInputRef.current?.click()}>
                <FolderOpen className="h-3.5 w-3.5 mr-1" /> Chọn file JSON
              </Button>
              <span className="text-xs text-vintage-dark/40 self-center">hoặc paste nội dung bên dưới</span>
            </div>
            <textarea
              className="w-full rounded-lg border border-blue-200 px-3 py-2 text-xs font-mono min-h-[100px] resize-y focus:outline-none focus:ring-2 focus:ring-blue-300 focus:border-blue-400 bg-white"
              placeholder='{"type": "service_account", "project_id": "...", "private_key": "...", "client_email": "..."}'
              value={jsonInput}
              onChange={(e) => setJsonInput(e.target.value)}
            />
          </div>

          <div>
            <label className="block text-xs font-medium mb-1">Folder ID (mặc định)</label>
            <Input
              placeholder="Lấy từ URL: drive.google.com/drive/folders/FOLDER_ID"
              value={folderIdInput}
              onChange={(e) => setFolderIdInput(e.target.value)}
              className="text-xs"
            />
          </div>

          <div className="flex gap-2">
            <Button size="sm" variant="outline" onClick={handleTest} disabled={testing || !jsonInput.trim()}>
              {testing ? <Loader2 className="h-3.5 w-3.5 animate-spin mr-1" /> : <RefreshCw className="h-3.5 w-3.5 mr-1" />}
              Test kết nối
            </Button>
            <Button size="sm" onClick={handleSave} disabled={saving || !jsonInput.trim()}>
              {saving ? <Loader2 className="h-3.5 w-3.5 animate-spin mr-1" /> : <Shield className="h-3.5 w-3.5 mr-1" />}
              Lưu credentials
            </Button>
          </div>

          {testResult && (
            <div className={`p-2 rounded-lg text-xs ${testResult.connected ? 'bg-green-50 border border-green-200 text-green-700' : 'bg-red-50 border border-red-200 text-red-700'}`}>
              {testResult.connected ? (
                <div className="space-y-0.5">
                  <p className="font-bold flex items-center gap-1"><CheckCircle className="h-3 w-3" /> Kết nối thành công!</p>
                  <p>Email: <span className="font-mono">{testResult.email}</span></p>
                </div>
              ) : (
                <p className="flex items-center gap-1"><AlertCircle className="h-3 w-3" /> {testResult.error}</p>
              )}
            </div>
          )}

          {message && !testResult && (
            <p className={`text-xs ${message.startsWith('✅') ? 'text-green-600' : message.startsWith('❌') ? 'text-red-500' : 'text-amber-600'}`}>
              {message}
            </p>
          )}
        </div>
      )}
    </div>
  );
}


// ============================================================================
// SaveServerKeySection — Save Gemini key to server config (admin)
// ============================================================================
function SaveServerKeySection({ onSaved }: { onSaved: () => void }) {
  const [serverKey, setServerKey] = useState('');
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState('');

  const handleSaveToServer = async () => {
    if (!serverKey.trim()) return;
    setSaving(true);
    setMessage('');
    try {
      const token = localStorage.getItem('token');
      const res = await axios.post('/media-stream/api/gemini-key/', {
        gemini_api_key: serverKey.trim(),
      }, {
        headers: {
          'Content-Type': 'application/json',
          ...(token ? { Authorization: `Token ${token}` } : {}),
        },
      });
      setMessage(res.data.message || 'Đã lưu');
      setServerKey('');
      onSaved();
    } catch (err: unknown) {
      const msg = axios.isAxiosError(err) ? err.response?.data?.error : 'Lỗi lưu key';
      setMessage(String(msg));
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="pt-2 border-t border-vintage-tan/20">
      <p className="text-xs font-medium text-vintage-dark/70 mb-1.5">
        Lưu key vào server (dùng chung cho tất cả user):
      </p>
      <div className="flex gap-2">
        <Input
          type="password"
          placeholder="AIza... (Gemini API key)"
          value={serverKey}
          onChange={(e) => setServerKey(e.target.value)}
          className="flex-1 text-xs"
        />
        <Button size="sm" onClick={handleSaveToServer} disabled={saving || !serverKey.trim()}>
          {saving ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : 'Lưu server'}
        </Button>
      </div>
      {message && (
        <p className={`text-xs mt-1 ${message.includes('Lỗi') ? 'text-red-500' : 'text-green-600'}`}>
          {message}
        </p>
      )}
    </div>
  );
}
