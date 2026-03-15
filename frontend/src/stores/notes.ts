import { defineStore } from 'pinia'
import apiClient from '@/api/client'

export type LayoutType = 
  | 'text-only'       // 纯文字
  | 'image-top'       // 单图-上
  | 'image-bottom'    // 单图-下
  | 'split-left'      // 多图-左图右文
  | 'split-right'     // 多图-右图左文
  | 'gallery-grid';   // 多图-照片墙

export interface NoteBlock {
  id: string;
  type: LayoutType;
  content: string;    // 文字内容
  images: string[];   // 图片URL数组
  mediaIds?: number[]; // 关联的媒体ID
}

export interface Note {
  id: string;
  title: string;
  summary?: string;
  createdAt: number;
  blocks: NoteBlock[]; // 笔记由多个块组成
  theme: 'book-classic' | 'modern-dark'; // 支持“像书一样”的主题
}

export const useNotesStore = defineStore('notes', {
  state: () => ({
    notes: [] as Note[],
    loading: false,
    error: null as string | null,
  }),
  actions: {
    async fetchNotes() {
      this.loading = true;
      try {
        const response = await apiClient.get('/notes/', {
          params: {
            limit: 100 // Increase limit to ensure we see the new note
          }
        });
        this.notes = response.data.data.items.map((n: any) => ({
          id: n.id.toString(),
          title: n.title,
          summary: n.summary,
          createdAt: new Date(n.created_at).getTime(),
          theme: n.book_theme || 'book-classic',
          blocks: [],
        }));
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
          title: data.title,
          createdAt: new Date(data.created_at).getTime(),
          theme: data.book_theme || 'book-classic',
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
            };
          }),
        };

        const index = this.notes.findIndex(n => n.id === id);
        if (index !== -1) {
          this.notes[index] = note;
        } else {
          this.notes.push(note);
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
      const file = new File([blob], "image.jpg", { type: "image/jpeg" });

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
        });
        const newNoteId = noteRes.data.data.id;

        // 2. Save Content (Blocks)
        if (note.blocks && note.blocks.length > 0) {
          await this.saveNoteContent(newNoteId.toString(), note.blocks, note);
        }

        await this.fetchNotes();
        return newNoteId.toString();
      } catch (err: any) {
        this.error = err.message;
        throw err;
      }
    },

    async publishNote(id: string) {
      try {
        await apiClient.post(`/notes/${id}/publish`);
        await this.fetchNotes();
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
          await this.saveNoteContent(id, updatedNote.blocks, updatedNote);
        }
        
        // Refresh local
        await this.getNoteById(id);
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
    },

    async deleteNote(id: string) {
      try {
        await apiClient.delete(`/notes/${id}`);
        this.notes = this.notes.filter(n => n.id !== id);
      } catch (err: any) {
        this.error = err.message;
        throw err;
      }
    },
  }
})
