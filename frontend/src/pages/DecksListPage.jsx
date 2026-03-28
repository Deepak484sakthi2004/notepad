import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Plus, BookOpen, Search } from 'lucide-react';
import TopBar from '@/components/layout/TopBar';
import Button from '@/components/ui/Button';
import EmptyState from '@/components/ui/EmptyState';
import ConfirmDialog from '@/components/ui/ConfirmDialog';
import Modal from '@/components/ui/Modal';
import Input from '@/components/ui/Input';
import Spinner from '@/components/ui/Spinner';
import DeckCard from '@/flashcards/DeckCard';
import { useFlashcardStore } from '@/store/flashcardStore';
import { createDeck, deleteDeck } from '@/api/flashcards';
import toast from 'react-hot-toast';

export default function DecksListPage() {
  const navigate = useNavigate();
  const { decks, isLoading, fetchDecks, addDeck, removeDeck } = useFlashcardStore();
  const [search, setSearch] = useState('');
  const [showCreate, setShowCreate] = useState(false);
  const [newDeckName, setNewDeckName] = useState('');
  const [isCreating, setIsCreating] = useState(false);
  const [deleteTarget, setDeleteTarget] = useState(null);
  const [isDeleting, setIsDeleting] = useState(false);

  useEffect(() => {
    fetchDecks();
  }, []);

  const filtered = decks.filter((d) =>
    d.name.toLowerCase().includes(search.toLowerCase())
  );

  const handleCreate = async () => {
    if (!newDeckName.trim()) return;
    setIsCreating(true);
    try {
      const res = await createDeck({ name: newDeckName });
      addDeck(res.data.deck);
      toast.success('Deck created');
      setShowCreate(false);
      setNewDeckName('');
      navigate(`/decks/${res.data.deck.id}`);
    } catch {
      toast.error('Failed to create deck');
    } finally {
      setIsCreating(false);
    }
  };

  const handleDelete = async () => {
    if (!deleteTarget) return;
    setIsDeleting(true);
    try {
      await deleteDeck(deleteTarget.id);
      removeDeck(deleteTarget.id);
      toast.success('Deck deleted');
    } catch {
      toast.error('Failed to delete deck');
    } finally {
      setIsDeleting(false);
      setDeleteTarget(null);
    }
  };

  return (
    <div className="flex flex-col h-full">
      <TopBar
        title="Flashcard Decks"
        actions={
          <Button size="sm" icon={<Plus size={15} />} onClick={() => setShowCreate(true)}>
            New deck
          </Button>
        }
      />

      <div className="flex-1 overflow-y-auto p-6">
        {isLoading ? (
          <div className="flex justify-center py-16">
            <Spinner size="lg" />
          </div>
        ) : (
          <div className="max-w-4xl mx-auto">
            {decks.length > 0 && (
              <div className="relative mb-6">
                <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
                <input
                  type="text"
                  placeholder="Search decks…"
                  value={search}
                  onChange={(e) => setSearch(e.target.value)}
                  className="w-full pl-9 pr-4 py-2.5 text-sm border border-gray-200 rounded-xl focus:outline-none focus:border-indigo-400 focus:ring-2 focus:ring-indigo-100"
                />
              </div>
            )}

            {filtered.length === 0 && decks.length === 0 ? (
              <EmptyState
                icon={<BookOpen size={48} />}
                title="No decks yet"
                description="Create a deck manually or generate one from any note"
                action={
                  <Button icon={<Plus size={16} />} onClick={() => setShowCreate(true)}>
                    Create deck
                  </Button>
                }
              />
            ) : filtered.length === 0 ? (
              <EmptyState
                icon={<Search size={48} />}
                title="No results"
                description={`No decks match "${search}"`}
              />
            ) : (
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
                {filtered.map((deck) => (
                  <DeckCard
                    key={deck.id}
                    deck={deck}
                    onDelete={(d) => setDeleteTarget(d)}
                  />
                ))}
              </div>
            )}
          </div>
        )}
      </div>

      <Modal isOpen={showCreate} onClose={() => setShowCreate(false)} title="New deck" size="sm">
        <div className="flex flex-col gap-4">
          <Input
            label="Deck name"
            value={newDeckName}
            onChange={(e) => setNewDeckName(e.target.value)}
            placeholder="e.g. Algorithms, Chapter 3…"
            onKeyDown={(e) => e.key === 'Enter' && handleCreate()}
            autoFocus
          />
          <div className="flex gap-3">
            <Button variant="secondary" className="flex-1" onClick={() => setShowCreate(false)}>
              Cancel
            </Button>
            <Button
              className="flex-1"
              onClick={handleCreate}
              loading={isCreating}
              disabled={!newDeckName.trim()}
            >
              Create
            </Button>
          </div>
        </div>
      </Modal>

      <ConfirmDialog
        isOpen={!!deleteTarget}
        onClose={() => setDeleteTarget(null)}
        onConfirm={handleDelete}
        isLoading={isDeleting}
        title="Delete deck?"
        message={`"${deleteTarget?.name}" and all its cards will be permanently deleted.`}
        confirmLabel="Delete"
      />
    </div>
  );
}
