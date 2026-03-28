import React, { useEffect, useState } from 'react';
import { Plus, Tag, Pencil, Trash2 } from 'lucide-react';
import TopBar from '@/components/layout/TopBar';
import Button from '@/components/ui/Button';
import Input from '@/components/ui/Input';
import Modal from '@/components/ui/Modal';
import EmptyState from '@/components/ui/EmptyState';
import Badge from '@/components/ui/Badge';
import ConfirmDialog from '@/components/ui/ConfirmDialog';
import { useWorkspaceStore } from '@/store/workspaceStore';
import { createTag, getTags } from '@/api/workspaces';
import apiClient from '@/api/client';
import toast from 'react-hot-toast';

const PRESET_COLORS = [
  '#6366f1', '#8b5cf6', '#ec4899', '#ef4444',
  '#f59e0b', '#10b981', '#14b8a6', '#3b82f6',
];

export default function TagsPage() {
  const { activeWorkspaceId, tags, fetchTags, addTag } = useWorkspaceStore();
  const [isLoading, setIsLoading] = useState(true);
  const [showCreate, setShowCreate] = useState(false);
  const [editTag, setEditTag] = useState(null);
  const [deleteTag, setDeleteTag] = useState(null);
  const [form, setForm] = useState({ name: '', colour: '#6366f1' });
  const [isSaving, setIsSaving] = useState(false);
  const [isDeleting, setIsDeleting] = useState(false);

  useEffect(() => {
    if (activeWorkspaceId) {
      fetchTags(activeWorkspaceId).finally(() => setIsLoading(false));
    }
  }, [activeWorkspaceId]);

  const resetForm = () => setForm({ name: '', colour: '#6366f1' });

  const handleCreate = async () => {
    if (!form.name.trim()) return;
    setIsSaving(true);
    try {
      const res = await createTag(activeWorkspaceId, form);
      addTag(res.data.tag);
      toast.success('Tag created');
      setShowCreate(false);
      resetForm();
    } catch (err) {
      toast.error(err.response?.data?.error || 'Failed to create tag');
    } finally {
      setIsSaving(false);
    }
  };

  const handleUpdate = async () => {
    if (!editTag) return;
    setIsSaving(true);
    try {
      await apiClient.put(`/api/tags/${editTag.id}`, form);
      const updated = useWorkspaceStore.getState().tags.map((t) =>
        t.id === editTag.id ? { ...t, ...form } : t
      );
      useWorkspaceStore.setState({ tags: updated });
      toast.success('Tag updated');
      setEditTag(null);
      resetForm();
    } catch {
      toast.error('Failed to update tag');
    } finally {
      setIsSaving(false);
    }
  };

  const handleDelete = async () => {
    if (!deleteTag) return;
    setIsDeleting(true);
    try {
      await apiClient.delete(`/api/tags/${deleteTag.id}`);
      useWorkspaceStore.setState({
        tags: useWorkspaceStore.getState().tags.filter((t) => t.id !== deleteTag.id),
      });
      toast.success('Tag deleted');
    } catch {
      toast.error('Failed to delete tag');
    } finally {
      setIsDeleting(false);
      setDeleteTag(null);
    }
  };

  const openEdit = (tag) => {
    setForm({ name: tag.name, colour: tag.colour });
    setEditTag(tag);
  };

  return (
    <div className="flex flex-col h-full">
      <TopBar
        title="Tags"
        actions={
          <Button
            size="sm"
            icon={<Plus size={15} />}
            onClick={() => { resetForm(); setShowCreate(true); }}
          >
            New tag
          </Button>
        }
      />

      <div className="flex-1 overflow-y-auto p-6">
        {tags.length === 0 ? (
          <EmptyState
            icon={<Tag size={48} />}
            title="No tags yet"
            description="Tags help you organise and filter your pages"
            action={
              <Button icon={<Plus size={16} />} onClick={() => setShowCreate(true)}>
                Create tag
              </Button>
            }
          />
        ) : (
          <div className="max-w-2xl mx-auto">
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              {tags.map((tag) => (
                <div
                  key={tag.id}
                  className="flex items-center gap-3 bg-white border border-gray-100 rounded-xl px-4 py-3 shadow-sm group"
                >
                  <div
                    className="w-4 h-4 rounded-full flex-shrink-0"
                    style={{ backgroundColor: tag.colour }}
                  />
                  <span className="flex-1 text-sm font-medium text-gray-900">{tag.name}</span>
                  <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                    <button
                      onClick={() => openEdit(tag)}
                      className="p-1.5 rounded-lg hover:bg-gray-100 text-gray-400 hover:text-gray-700"
                    >
                      <Pencil size={13} />
                    </button>
                    <button
                      onClick={() => setDeleteTag(tag)}
                      className="p-1.5 rounded-lg hover:bg-red-50 text-gray-400 hover:text-red-600"
                    >
                      <Trash2 size={13} />
                    </button>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Create / Edit Modal */}
      <Modal
        isOpen={showCreate || !!editTag}
        onClose={() => { setShowCreate(false); setEditTag(null); resetForm(); }}
        title={editTag ? 'Edit tag' : 'Create tag'}
        size="sm"
      >
        <div className="flex flex-col gap-4">
          <Input
            label="Tag name"
            value={form.name}
            onChange={(e) => setForm((f) => ({ ...f, name: e.target.value }))}
            placeholder="e.g. Important"
          />
          <div>
            <label className="text-sm font-medium text-gray-700 block mb-2">Colour</label>
            <div className="flex items-center gap-2 flex-wrap">
              {PRESET_COLORS.map((c) => (
                <button
                  key={c}
                  onClick={() => setForm((f) => ({ ...f, colour: c }))}
                  className={`w-7 h-7 rounded-full transition-transform ${
                    form.colour === c ? 'scale-125 ring-2 ring-offset-1 ring-gray-400' : ''
                  }`}
                  style={{ backgroundColor: c }}
                />
              ))}
              <input
                type="color"
                value={form.colour}
                onChange={(e) => setForm((f) => ({ ...f, colour: e.target.value }))}
                className="w-7 h-7 rounded cursor-pointer"
              />
            </div>
          </div>
          <div className="flex gap-3 pt-1">
            <Button
              variant="secondary"
              className="flex-1"
              onClick={() => { setShowCreate(false); setEditTag(null); }}
            >
              Cancel
            </Button>
            <Button
              className="flex-1"
              onClick={editTag ? handleUpdate : handleCreate}
              loading={isSaving}
              disabled={!form.name.trim()}
            >
              {editTag ? 'Save changes' : 'Create'}
            </Button>
          </div>
        </div>
      </Modal>

      <ConfirmDialog
        isOpen={!!deleteTag}
        onClose={() => setDeleteTag(null)}
        onConfirm={handleDelete}
        isLoading={isDeleting}
        title="Delete tag?"
        message={`The tag "${deleteTag?.name}" will be removed from all pages.`}
        confirmLabel="Delete"
      />
    </div>
  );
}
