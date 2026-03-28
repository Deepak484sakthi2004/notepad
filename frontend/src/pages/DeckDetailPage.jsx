import React, { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  Play, RotateCcw, Trash2, Flag, PauseCircle, Plus, ArrowLeft, Sparkles,
} from 'lucide-react';
import TopBar from '@/components/layout/TopBar';
import Button from '@/components/ui/Button';
import Badge from '@/components/ui/Badge';
import ConfirmDialog from '@/components/ui/ConfirmDialog';
import Modal from '@/components/ui/Modal';
import Input from '@/components/ui/Input';
import EmptyState from '@/components/ui/EmptyState';
import Spinner from '@/components/ui/Spinner';
import { getDeck, getDeckCards, createCard, deleteCard, suspendCard, flagCard, regenerateDeck } from '@/api/flashcards';
import { difficultyLabel, difficultyColor, classNames } from '@/utils/helpers';
import toast from 'react-hot-toast';

export default function DeckDetailPage() {
  const { deckId } = useParams();
  const navigate = useNavigate();
  const [deck, setDeck] = useState(null);
  const [cards, setCards] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [showAddCard, setShowAddCard] = useState(false);
  const [newCard, setNewCard] = useState({ question: '', answer: '' });
  const [isSaving, setIsSaving] = useState(false);
  const [deleteTarget, setDeleteTarget] = useState(null);
  const [isDeleting, setIsDeleting] = useState(false);
  const [isRegenerating, setIsRegenerating] = useState(false);

  useEffect(() => {
    loadDeck();
  }, [deckId]);

  const loadDeck = async () => {
    setIsLoading(true);
    try {
      const [deckRes, cardsRes] = await Promise.all([
        getDeck(deckId),
        getDeckCards(deckId),
      ]);
      setDeck(deckRes.data.deck);
      setCards(cardsRes.data.cards);
    } catch {
      toast.error('Failed to load deck');
      navigate('/decks');
    } finally {
      setIsLoading(false);
    }
  };

  const handleAddCard = async () => {
    if (!newCard.question.trim() || !newCard.answer.trim()) return;
    setIsSaving(true);
    try {
      const res = await createCard(deckId, newCard);
      setCards((c) => [...c, res.data.card]);
      toast.success('Card added');
      setShowAddCard(false);
      setNewCard({ question: '', answer: '' });
    } catch {
      toast.error('Failed to add card');
    } finally {
      setIsSaving(false);
    }
  };

  const handleDeleteCard = async () => {
    if (!deleteTarget) return;
    setIsDeleting(true);
    try {
      await deleteCard(deleteTarget.id);
      setCards((c) => c.filter((card) => card.id !== deleteTarget.id));
      toast.success('Card deleted');
    } catch {
      toast.error('Failed to delete card');
    } finally {
      setIsDeleting(false);
      setDeleteTarget(null);
    }
  };

  const handleToggleSuspend = async (card) => {
    try {
      const res = await suspendCard(card.id);
      setCards((c) => c.map((ca) => (ca.id === card.id ? res.data.card : ca)));
    } catch {
      toast.error('Failed to update card');
    }
  };

  const handleToggleFlag = async (card) => {
    try {
      const res = await flagCard(card.id);
      setCards((c) => c.map((ca) => (ca.id === card.id ? res.data.card : ca)));
    } catch {
      toast.error('Failed to update card');
    }
  };

  const handleRegenerate = async () => {
    if (!deck?.source_page_id) {
      toast.error('No source page to regenerate from');
      return;
    }
    if (!confirm('Regenerate all cards? Existing cards will be replaced.')) return;
    setIsRegenerating(true);
    try {
      const res = await regenerateDeck(deckId, { num_cards: 10 });
      toast.success('Deck regenerated!');
      await loadDeck();
    } catch (err) {
      toast.error(err.response?.data?.error || 'Regeneration failed');
    } finally {
      setIsRegenerating(false);
    }
  };

  if (isLoading) {
    return (
      <div className="flex-1 flex items-center justify-center">
        <Spinner size="lg" />
      </div>
    );
  }

  return (
    <div className="flex flex-col h-full">
      <TopBar
        actions={
          <div className="flex items-center gap-2">
            <Button
              variant="secondary"
              size="sm"
              icon={<ArrowLeft size={14} />}
              onClick={() => navigate('/decks')}
            >
              Back
            </Button>
            {deck?.source_page_id && (
              <Button
                variant="secondary"
                size="sm"
                icon={<RotateCcw size={14} />}
                onClick={handleRegenerate}
                loading={isRegenerating}
              >
                Regenerate
              </Button>
            )}
            <Button
              size="sm"
              icon={<Plus size={14} />}
              onClick={() => setShowAddCard(true)}
              variant="secondary"
            >
              Add card
            </Button>
            <Button
              size="sm"
              icon={<Play size={14} />}
              onClick={() => navigate(`/study/${deckId}`)}
            >
              Study
            </Button>
          </div>
        }
      />

      <div className="flex-1 overflow-y-auto p-6">
        <div className="max-w-3xl mx-auto">
          <div className="mb-6">
            <h1 className="text-2xl font-bold text-gray-900">{deck?.name}</h1>
            {deck?.description && (
              <p className="text-gray-500 mt-1">{deck.description}</p>
            )}
            <div className="mt-2 flex items-center gap-3 text-sm text-gray-400">
              <span>{cards.length} cards</span>
              {deck?.auto_generated && (
                <Badge variant="indigo">
                  <Sparkles size={10} /> AI generated
                </Badge>
              )}
            </div>
          </div>

          {cards.length === 0 ? (
            <EmptyState
              icon={<Plus size={48} />}
              title="No cards yet"
              description="Add cards manually or regenerate from the source page"
              action={
                <Button icon={<Plus size={16} />} onClick={() => setShowAddCard(true)}>
                  Add card
                </Button>
              }
            />
          ) : (
            <div className="space-y-3">
              {cards.map((card) => (
                <div
                  key={card.id}
                  className={classNames(
                    'bg-white rounded-xl border p-4 shadow-sm',
                    card.is_suspended ? 'opacity-50 border-gray-100' : 'border-gray-200'
                  )}
                >
                  <div className="flex items-start gap-3">
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 mb-1 flex-wrap">
                        <Badge className={classNames('text-xs', difficultyColor(card.difficulty))}>
                          {difficultyLabel(card.difficulty)}
                        </Badge>
                        <span className="text-xs text-gray-400 bg-gray-50 px-2 py-0.5 rounded-full">
                          {card.question_type || 'recall'}
                        </span>
                        {card.is_flagged && (
                          <span className="text-xs text-amber-600 flex items-center gap-1">
                            <Flag size={10} /> Flagged
                          </span>
                        )}
                      </div>
                      <p className="text-sm font-medium text-gray-900 mb-2">{card.question}</p>
                      <p className="text-sm text-gray-600">{card.answer}</p>
                      {card.source_snippet && (
                        <p className="text-xs text-gray-400 italic mt-2 border-l-2 border-gray-200 pl-2">
                          {card.source_snippet}
                        </p>
                      )}
                    </div>
                    <div className="flex items-center gap-1 flex-shrink-0">
                      <button
                        onClick={() => handleToggleFlag(card)}
                        className={`p-1.5 rounded-lg transition-colors ${
                          card.is_flagged
                            ? 'text-amber-500 bg-amber-50'
                            : 'text-gray-400 hover:text-amber-500 hover:bg-amber-50'
                        }`}
                        title="Flag"
                      >
                        <Flag size={13} />
                      </button>
                      <button
                        onClick={() => handleToggleSuspend(card)}
                        className={`p-1.5 rounded-lg transition-colors ${
                          card.is_suspended
                            ? 'text-gray-500 bg-gray-100'
                            : 'text-gray-400 hover:text-gray-600 hover:bg-gray-100'
                        }`}
                        title={card.is_suspended ? 'Unsuspend' : 'Suspend'}
                      >
                        <PauseCircle size={13} />
                      </button>
                      <button
                        onClick={() => setDeleteTarget(card)}
                        className="p-1.5 rounded-lg text-gray-400 hover:text-red-600 hover:bg-red-50 transition-colors"
                        title="Delete"
                      >
                        <Trash2 size={13} />
                      </button>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      <Modal isOpen={showAddCard} onClose={() => setShowAddCard(false)} title="Add card" size="md">
        <div className="flex flex-col gap-4">
          <div>
            <label className="text-sm font-medium text-gray-700 block mb-1">Question</label>
            <textarea
              value={newCard.question}
              onChange={(e) => setNewCard((c) => ({ ...c, question: e.target.value }))}
              placeholder="Enter the question…"
              rows={3}
              className="w-full text-sm border border-gray-200 rounded-lg px-3 py-2 resize-none focus:outline-none focus:border-indigo-400 focus:ring-2 focus:ring-indigo-100"
            />
          </div>
          <div>
            <label className="text-sm font-medium text-gray-700 block mb-1">Answer</label>
            <textarea
              value={newCard.answer}
              onChange={(e) => setNewCard((c) => ({ ...c, answer: e.target.value }))}
              placeholder="Enter the answer…"
              rows={3}
              className="w-full text-sm border border-gray-200 rounded-lg px-3 py-2 resize-none focus:outline-none focus:border-indigo-400 focus:ring-2 focus:ring-indigo-100"
            />
          </div>
          <div className="flex gap-3">
            <Button variant="secondary" className="flex-1" onClick={() => setShowAddCard(false)}>
              Cancel
            </Button>
            <Button
              className="flex-1"
              onClick={handleAddCard}
              loading={isSaving}
              disabled={!newCard.question.trim() || !newCard.answer.trim()}
            >
              Add card
            </Button>
          </div>
        </div>
      </Modal>

      <ConfirmDialog
        isOpen={!!deleteTarget}
        onClose={() => setDeleteTarget(null)}
        onConfirm={handleDeleteCard}
        isLoading={isDeleting}
        title="Delete card?"
        message="This card and its review history will be permanently deleted."
        confirmLabel="Delete"
      />
    </div>
  );
}
