import React, { useEffect, useCallback, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { ArrowLeft, Sparkles, CheckCircle } from 'lucide-react';
import CardFlip from '@/flashcards/CardFlip';
import RatingBar from '@/flashcards/RatingBar';
import AskAIPanel from '@/flashcards/AskAIPanel';
import Spinner from '@/components/ui/Spinner';
import Button from '@/components/ui/Button';
import { useFlashcardStore } from '@/store/flashcardStore';
import toast from 'react-hot-toast';

export default function StudySessionPage() {
  const { deckId } = useParams();
  const navigate = useNavigate();
  const {
    session,
    sessionCards,
    currentCardIndex,
    isFlipped,
    sessionStats,
    startStudySession,
    flipCard,
    rateCard,
    endStudySession,
  } = useFlashcardStore();

  const [isLoading, setIsLoading] = useState(true);
  const [isDone, setIsDone] = useState(false);
  const [showAI, setShowAI] = useState(false);
  const [isRating, setIsRating] = useState(false);

  useEffect(() => {
    loadSession();
    return () => {
      // Clean up on unmount if session is active
    };
  }, [deckId]);

  useEffect(() => {
    const handler = (e) => {
      if (e.key === ' ' || e.key === 'Enter') {
        e.preventDefault();
        if (!isFlipped) flipCard();
      }
      if (isFlipped && !isRating) {
        if (['1', '2', '3', '4', '5'].includes(e.key)) {
          handleRate(parseInt(e.key));
        }
      }
    };
    window.addEventListener('keydown', handler);
    return () => window.removeEventListener('keydown', handler);
  }, [isFlipped, isRating]);

  const loadSession = async () => {
    setIsLoading(true);
    try {
      const { cards } = await startStudySession(deckId);
      if (cards.length === 0) {
        toast.success("Nothing due — you're all caught up!");
        setIsDone(true);
      }
    } catch (err) {
      toast.error('Failed to start study session');
      navigate('/decks');
    } finally {
      setIsLoading(false);
    }
  };

  const handleRate = async (quality) => {
    if (isRating) return;
    setIsRating(true);
    try {
      const done = await rateCard(quality);
      if (done) {
        await endStudySession();
        setIsDone(true);
      }
    } finally {
      setIsRating(false);
    }
  };

  const handleFinish = async () => {
    await endStudySession();
    navigate(`/decks/${deckId}`);
  };

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <Spinner size="xl" />
      </div>
    );
  }

  // Done screen
  if (isDone) {
    const accuracy =
      sessionStats.reviewed > 0
        ? Math.round((sessionStats.correct / sessionStats.reviewed) * 100)
        : 0;

    return (
      <div className="min-h-screen bg-gradient-to-br from-indigo-50 to-white flex flex-col items-center justify-center p-6">
        <div className="bg-white rounded-3xl shadow-xl border border-gray-100 p-10 max-w-md w-full text-center">
          <div className="w-16 h-16 rounded-full bg-green-100 flex items-center justify-center mx-auto mb-4">
            <CheckCircle size={32} className="text-green-600" />
          </div>
          <h2 className="text-2xl font-bold text-gray-900 mb-2">Session complete!</h2>
          <p className="text-gray-500 mb-6">Great work — keep it up!</p>

          <div className="grid grid-cols-2 gap-4 mb-8">
            <div className="bg-gray-50 rounded-2xl p-4">
              <div className="text-2xl font-bold text-gray-900">{sessionStats.reviewed}</div>
              <div className="text-sm text-gray-500">Cards reviewed</div>
            </div>
            <div className="bg-gray-50 rounded-2xl p-4">
              <div className="text-2xl font-bold text-green-600">{accuracy}%</div>
              <div className="text-sm text-gray-500">Accuracy</div>
            </div>
          </div>

          <div className="flex gap-3">
            <Button
              variant="secondary"
              className="flex-1"
              onClick={() => navigate('/decks')}
            >
              All decks
            </Button>
            <Button
              className="flex-1"
              onClick={() => { setIsDone(false); loadSession(); }}
            >
              Study again
            </Button>
          </div>
        </div>
      </div>
    );
  }

  const currentCard = sessionCards[currentCardIndex];
  const progress = sessionCards.length > 0
    ? ((currentCardIndex / sessionCards.length) * 100)
    : 0;

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-indigo-50 flex flex-col">
      {/* Header */}
      <header className="flex items-center justify-between px-6 py-4">
        <button
          onClick={handleFinish}
          className="flex items-center gap-2 text-sm text-gray-600 hover:text-gray-900 transition-colors"
        >
          <ArrowLeft size={16} />
          Exit
        </button>
        <div className="text-sm text-gray-500">
          {currentCardIndex + 1} / {sessionCards.length}
        </div>
        <button
          onClick={() => setShowAI((v) => !v)}
          className="flex items-center gap-1.5 text-sm text-indigo-600 hover:text-indigo-800"
        >
          <Sparkles size={14} />
          Ask AI
        </button>
      </header>

      {/* Progress bar */}
      <div className="h-1 bg-gray-200 mx-6 rounded-full overflow-hidden">
        <div
          className="h-full bg-indigo-500 rounded-full transition-all duration-300"
          style={{ width: `${progress}%` }}
        />
      </div>

      {/* Session stats */}
      <div className="flex justify-center gap-6 mt-3 text-xs text-gray-500">
        <span className="text-green-600 font-medium">{sessionStats.correct} correct</span>
        <span>{sessionStats.reviewed} reviewed</span>
        <span>{sessionCards.length - currentCardIndex} remaining</span>
      </div>

      {/* Main content */}
      <div className="flex-1 flex flex-col items-center justify-center px-6 py-8 gap-6">
        <div className="w-full max-w-lg">
          <CardFlip card={currentCard} isFlipped={isFlipped} onFlip={flipCard} />
        </div>

        {/* Controls */}
        {!isFlipped ? (
          <button
            onClick={flipCard}
            className="px-8 py-3 bg-white border-2 border-gray-200 hover:border-indigo-400 text-gray-700 font-medium rounded-2xl text-sm transition-colors shadow-sm"
          >
            Show Answer
            <span className="ml-2 text-gray-400 text-xs font-normal">Space</span>
          </button>
        ) : (
          <div className="flex flex-col items-center gap-3">
            <p className="text-xs text-gray-500">How well did you know this?</p>
            <RatingBar onRate={handleRate} disabled={isRating} />
            <p className="text-xs text-gray-400 mt-1">
              Press 1–5 to rate · Space to flip
            </p>
          </div>
        )}
      </div>

      {/* AI Panel */}
      {showAI && currentCard && (
        <div className="fixed bottom-6 right-6 w-96 z-30">
          <AskAIPanel card={currentCard} onClose={() => setShowAI(false)} />
        </div>
      )}
    </div>
  );
}
