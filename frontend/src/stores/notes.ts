import { defineStore } from 'pinia'
import apiClient from '../api/client'

export type LayoutType = 
  | 'text-only'       // 纯文字
  | 'image-top'       // 单图-上
  | 'image-bottom'    // 单图-下
  | 'split-left'      // 多图-左图右文
  | 'split-right'     // 多图-右图左文
  | 'gallery-grid';   // 多图-照片墙

export type GalleryTemplate =
  | 'grid'
  | 'mosaic'
  | 'spotlight'
  | 'film'
  | 'heart';

export interface NoteBlock {
  id: string;
  type: LayoutType;
  content: string;    // 文字内容
  images: string[];   // 图片URL数组
  mediaIds?: number[]; // 关联的媒体ID
  galleryTemplate?: GalleryTemplate;
}

export interface Note {
  id: string;
  userId?: number;
  authorUsername?: string;
  authorNickname?: string;
  authorAvatarUrl?: string;
  commentCount?: number;
  hotComment?: {
    id: number;
    user_id: number;
    nickname: string;
    username: string;
    content: string;
    created_at: string;
  } | null;
  title: string;
  summary?: string;
  /** 心情 key：happy | love | calm | sad | excited | meh */
  mood?: string | null;
  /** Open-Meteo WMO weathercode，创建时快照 */
  weatherWmoCode?: number | null;
  createdAt: number;
  status?: string;
  isPrivate?: boolean;
  blocks: NoteBlock[]; // 笔记由多个块组成
  theme: 'book-classic' | 'modern-dark'; // 支持“像书一样”的主题
}

export const useNotesStore = defineStore('notes', {
  state: () => ({
    myNotes: [] as Note[],
    publicNotes: [] as Note[],
    followingNotes: [] as Note[],
    hotNotes: [] as Note[],
    loading: false,
    error: null as string | null,
  }),
  actions: {
    mapNoteSummary(n: any): Note {
      return {
        id: n.id.toString(),
        userId: n.user_id,
        authorUsername: n.author_username,
        authorNickname: n.author_nickname,
        authorAvatarUrl: n.author_avatar_url,
        commentCount: n.comment_count || 0,
        hotComment: n.hot_comment || null,
        title: n.title,
        summary: n.summary,
        mood: n.mood ?? null,
        weatherWmoCode: n.weather_wmo_code ?? null,
        createdAt: new Date(n.created_at).getTime(),
        theme: n.book_theme || 'book-classic',
        status: n.status,
        isPrivate: n.is_private,
        blocks: n.blocks ? n.blocks.map((b: any) => ({
          id: b.id.toString(),
          type: 'text-only',
          content: b.text_content || '',
          images: b.media_assets ? b.media_assets.map((m: any) => m.file_url) : [],
          mediaIds: b.media_assets ? b.media_assets.map((m: any) => m.id) : [],
          galleryTemplate: this.parseGalleryTemplate(b.caption),
        })) : [],
      }
    },

    async fetchMyNotes() {
      this.loading = true;
      try {
        const response = await apiClient.get('/notes/', {
          params: {
            limit: 100 // Increase limit to ensure we see the new note
          }
        });
        
        this.myNotes = response.data.data.items.map((n: any) => this.mapNoteSummary(n));
      } catch (err: any) {
        this.error = err.message;
      } finally {
        this.loading = false;
      }
    },

    async fetchPublicNotes() {
      this.loading = true;
      try {
        const response = await apiClient.get('/notes/public', {
          params: {
            limit: 100
          }
        });

        this.publicNotes = response.data.data.items.map((n: any) => this.mapNoteSummary(n));
      } catch (err: any) {
        this.error = err.message;
      } finally {
        this.loading = false;
      }
    },

    async fetchFollowingNotes() {
      this.loading = true;
      try {
        const response = await apiClient.get('/notes/following', {
          params: {
            limit: 100
          }
        });

        this.followingNotes = response.data.data.items.map((n: any) => this.mapNoteSummary(n));
      } catch (err: any) {
        this.error = err.message;
      } finally {
        this.loading = false;
      }
    },

    async fetchHotNotes() {
      this.loading = true;
      try {
        const response = await apiClient.get('/notes/hot', {
          params: {
            limit: 10
          }
        });

        this.hotNotes = response.data.data.items.map((n: any) => this.mapNoteSummary(n));
      } catch (err: any) {
        this.error = err.message;
      } finally {
        this.loading = false;
      }
    },

    async getNoteById(id: string) {
      try {
        const response = await apiClient.get(`/notes/detail/${id}`);
        const data = response.data.data;
        
        const note: Note = {
          id: data.id.toString(),
          userId: data.user_id,
          authorUsername: data.author_username,
          authorNickname: data.author_nickname,
          authorAvatarUrl: data.author_avatar_url,
          commentCount: data.comment_count || 0,
          hotComment: data.hot_comment || null,
          title: data.title,
          summary: data.summary,
          mood: data.mood ?? null,
          weatherWmoCode: data.weather_wmo_code ?? null,
          createdAt: new Date(data.created_at).getTime(),
          theme: data.book_theme || 'book-classic',
          status: data.status,
          isPrivate: data.is_private,
          blocks: data.blocks.map((b: any) => {
            // Map backend types back to frontend layout types
            let type: LayoutType = 'text-only';
            if (b.block_type === 'text') {
              type = 'text-only';
            } else if (b.block_type === 'gallery' && b.layout_style === 'photo_wall') {
              type = 'gallery-grid';
            } else if (b.block_type === 'image') {
              switch (b.layout_style) {
                case 'image_top': type = 'image-top'; break;
                case 'image_bottom': type = 'image-bottom'; break;
                case 'image_left_text_right': type = 'split-left'; break;
                case 'text_left_image_right': type = 'split-right'; break;
                default: type = 'image-top';
              }
            }

            return {
              id: b.id.toString(),
              type: type,
              content: b.text_content || '',
              images: b.media_assets.map((m: any) => m.file_url),
              mediaIds: b.media_assets.map((m: any) => m.id),
              galleryTemplate: this.parseGalleryTemplate(b.caption),
            };
          }),
        };

        const myIndex = this.myNotes.findIndex(n => n.id === id);
        if (myIndex !== -1) {
          this.myNotes[myIndex] = note;
        } else if (note.isPrivate || note.status !== 'published') {
          this.myNotes.push(note);
        }

        const publicIndex = this.publicNotes.findIndex(n => n.id === id);
        if (publicIndex !== -1) {
          if (note.status === 'published' && note.isPrivate === false) {
            this.publicNotes[publicIndex] = note;
          } else {
            this.publicNotes.splice(publicIndex, 1);
          }
        } else if (note.status === 'published' && note.isPrivate === false) {
          this.publicNotes.push(note);
        }

        const followingIndex = this.followingNotes.findIndex(n => n.id === id);
        if (followingIndex !== -1) {
          if (note.status === 'published' && note.isPrivate === false) {
            this.followingNotes[followingIndex] = note;
          } else {
            this.followingNotes.splice(followingIndex, 1);
          }
        }
        
        return note;
      } catch (err: any) {
        console.error('Failed to fetch note detail:', err);
        return undefined;
      }
    },

    async uploadImage(base64Data: string): Promise<number> {
      // Convert base64 to Blob
      const fetchResponse = await fetch(base64Data);
      const blob = await fetchResponse.blob();
      const mimeType = base64Data.match(/^data:(image\/[a-zA-Z0-9.+-]+);base64,/)?.[1] || blob.type || 'image/jpeg';
      const extensionMap: Record<string, string> = {
        'image/jpeg': 'jpg',
        'image/png': 'png',
        'image/webp': 'webp',
      };
      const extension = extensionMap[mimeType] || 'jpg';
      const file = new File([blob], `image.${extension}`, { type: mimeType });

      const formData = new FormData();
      formData.append('file', file);

      const response = await apiClient.post('/media-assets/upload/image', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });
      return response.data.data.id;
    },

    async addNote(note: Partial<Note>) {
      try {
        // 1. Create Note
        const summary = note.blocks 
          ? note.blocks.find(b => b.content?.trim())?.content.slice(0, 100) 
          : undefined;

        const noteRes = await apiClient.post('/notes/', {
          title: note.title,
          summary: summary,
          book_theme: note.theme,
          is_private: true,
          mood: note.mood ?? 'calm',
          weather_wmo_code: note.weatherWmoCode ?? null,
        });
        const newNoteId = noteRes.data.data.id;

        // 2. Save Content (Blocks)
        let firstMediaId = null;
        if (note.blocks && note.blocks.length > 0) {
          const processedBlocks = await this.saveNoteContent(newNoteId.toString(), note.blocks, note);
          
          // Find first media id from processed blocks to set as cover
           for (const block of processedBlocks) {
             if (block.media_ids && block.media_ids.length > 0) {
               firstMediaId = block.media_ids[0];
               break;
             }
           }
        }
        
        // 3. Update cover image if found
        if (firstMediaId) {
             await apiClient.put(`/notes/${newNoteId}`, {
                title: note.title,
                summary: summary,
                book_theme: note.theme,
                cover_media_id: firstMediaId
            });
        }

        await Promise.all([this.fetchMyNotes(), this.fetchPublicNotes(), this.fetchFollowingNotes(), this.fetchHotNotes()]);
        return newNoteId.toString();
      } catch (err: any) {
        this.error = err.message;
        throw err;
      }
    },

    async publishNote(id: string) {
      try {
        await apiClient.post(`/notes/${id}/publish`);
        await Promise.all([this.fetchMyNotes(), this.fetchPublicNotes(), this.fetchFollowingNotes(), this.fetchHotNotes()]);
      } catch (err: any) {
        this.error = err.message;
        throw err;
      }
    },

    async updateNote(id: string, updatedNote: Partial<Note>) {
      try {
        const summary = updatedNote.blocks 
          ? updatedNote.blocks.find(b => b.content?.trim())?.content.slice(0, 100) 
          : undefined;

        // Update metadata
        await apiClient.put(`/notes/${id}`, {
          title: updatedNote.title,
          summary: summary,
          book_theme: updatedNote.theme,
        });

        // Update content
        if (updatedNote.blocks) {
          const processedBlocks = await this.saveNoteContent(id, updatedNote.blocks, updatedNote);
           
          // Update cover image if needed (check if existing cover is valid, or set new one)
          // For simplicity, let's update cover if we have images and current cover is not set or we want to update it.
          // Let's find the first image in the note and set it as cover.
          let firstMediaId = null;
          for (const block of processedBlocks) {
             if (block.media_ids && block.media_ids.length > 0) {
               firstMediaId = block.media_ids[0];
               break;
             }
           }
           
           if (firstMediaId) {
                await apiClient.put(`/notes/${id}`, {
                    title: updatedNote.title,
                    summary: summary,
                    book_theme: updatedNote.theme,
                    cover_media_id: firstMediaId
                });
           }
        }
        
        // Refresh local
        await this.getNoteById(id);
        await Promise.all([this.fetchMyNotes(), this.fetchPublicNotes(), this.fetchFollowingNotes(), this.fetchHotNotes()]);
      } catch (err: any) {
        this.error = err.message;
        throw err;
      }
    },

    async saveNoteContent(noteId: string, blocks: NoteBlock[], noteMeta: Partial<Note>) {
      const processedBlocks = await Promise.all(blocks.map(async (block, index) => {
        let mediaIds = block.mediaIds || [];
        
        // Handle new images (base64)
        if (block.images && block.images.length > 0) {
          const newMediaIds = await Promise.all(block.images.map(async (img, imgIndex) => {
            if (img.startsWith('data:')) {
              return await this.uploadImage(img);
            }
            return mediaIds[imgIndex]; 
          }));
          mediaIds = newMediaIds.filter(id => id !== undefined) as number[];
        }

        // Map frontend layout types to backend block types and layout styles
        let blockType = 'text';
        let layoutStyle = 'normal';

        switch (block.type) {
          case 'text-only':
            blockType = 'text';
            layoutStyle = 'normal';
            break;
          case 'image-top':
            blockType = 'image';
            layoutStyle = 'image_top';
            break;
          case 'image-bottom':
            blockType = 'image';
            layoutStyle = 'image_bottom';
            break;
          case 'split-left':
            blockType = 'image';
            layoutStyle = 'image_left_text_right';
            break;
          case 'split-right':
            blockType = 'image';
            layoutStyle = 'text_left_image_right';
            break;
          case 'gallery-grid':
            blockType = 'gallery';
            layoutStyle = 'photo_wall';
            break;
        }

        return {
          block_type: blockType,
          sort_order: index,
          text_content: block.content,
          text_align: 'left',
          layout_style: layoutStyle,
          caption: block.type === 'gallery-grid'
            ? this.serializeGalleryTemplate(block.galleryTemplate)
            : undefined,
          media_ids: mediaIds,
        };
      }));

      const summary = blocks.find(b => b.content?.trim())?.content.slice(0, 100);

      await apiClient.put(`/notes/content/${noteId}`, {
        title: noteMeta.title,
        summary: summary,
        book_theme: noteMeta.theme,
        blocks: processedBlocks
      });
      
      return processedBlocks;
    },

    parseGalleryTemplate(caption?: string): GalleryTemplate {
      const value = caption?.startsWith('gallery_template:')
        ? caption.slice('gallery_template:'.length)
        : '';

      switch (value) {
        case 'mosaic':
        case 'spotlight':
        case 'film':
        case 'heart':
          return value;
        default:
          return 'grid';
      }
    },

    serializeGalleryTemplate(template?: GalleryTemplate) {
      return `gallery_template:${template || 'grid'}`;
    },

    async deleteNote(id: string) {
      try {
        await apiClient.delete(`/notes/${id}`);
        this.myNotes = this.myNotes.filter(n => n.id !== id);
        this.publicNotes = this.publicNotes.filter(n => n.id !== id);
        this.followingNotes = this.followingNotes.filter(n => n.id !== id);
        this.hotNotes = this.hotNotes.filter(n => n.id !== id);
      } catch (err: any) {
        this.error = err.message;
        throw err;
      }
    },
  }
})
