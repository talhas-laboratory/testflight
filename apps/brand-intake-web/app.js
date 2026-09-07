const questions = [
  {
    quote: '“People come to us because the alternatives make them feel like they are already behind.”',
    text: 'When customers feel “behind,” what do they believe they should already know or be able to do?',
  },
  {
    quote: '“We are for beginners, but I never want us to feel basic.”',
    text: 'What is the difference between being approachable and being simplistic for your Brand?',
  },
  {
    quote: '“The product gives them confidence—but confidence is such an overused word.”',
    text: 'What can a customer do after using the product that they were reluctant to do before?',
  },
  {
    quote: '“We should feel knowledgeable without looking like we are trying to prove it.”',
    text: 'What is one behaviour that would make the Brand feel performative rather than genuinely knowledgeable?',
  },
];

const evidence = {
  centre: {
    title: 'People move forward when complexity stops making them feel inadequate.',
    quotes: [
      ['“We make the first step feel like it belongs to you.”', 'Day 1 · written note'],
      ['“The category loves expertise more than it loves people.”', 'Day 2 · voice note'],
    ],
  },
  difference: {
    title: 'Guidance without the performance of expertise.',
    quotes: [
      ['“I want us to know a lot without needing the customer to notice how much we know.”', 'Day 1 · written note'],
      ['“No gatekeeping, and no dumbing down either.”', 'Clarification · answer 03'],
    ],
  },
  audience: {
    title: 'Capable beginners who distrust cultures of mastery.',
    quotes: [
      ['“They are not incapable. They just do not want to join the whole identity around it.”', 'Day 2 · voice note'],
      ['“Beginner might be the wrong word. They are entering on their own terms.”', 'Clarification · answer 01'],
    ],
  },
};

const note = document.querySelector('#brand-note');
const saveState = document.querySelector('#save-state');
const wordCount = document.querySelector('#word-count');
const sessionTime = document.querySelector('#session-time');
const recordButton = document.querySelector('#record-button');
const recordTime = document.querySelector('#record-time');
const attachmentInput = document.querySelector('#attachment-input');
const attachmentList = document.querySelector('#attachment-list');
const toast = document.querySelector('#toast');
let saveTimer;
let sessionSeconds = 0;
let recordingSeconds = 0;
let recordingTimer;
let questionIndex = 0;

const formatTime = (seconds) => `${String(Math.floor(seconds / 60)).padStart(2, '0')}:${String(seconds % 60).padStart(2, '0')}`;

function showToast(message) {
  toast.textContent = message;
  toast.classList.add('visible');
  window.clearTimeout(showToast.timer);
  showToast.timer = window.setTimeout(() => toast.classList.remove('visible'), 2600);
}

function switchView(view) {
  document.querySelectorAll('.screen').forEach((screen) => screen.classList.toggle('active', screen.dataset.screen === view));
  document.querySelectorAll('.view-switch').forEach((button) => button.classList.toggle('active', button.dataset.view === view));
  window.scrollTo({ top: 0, behavior: 'smooth' });
}

function updateWordCount() {
  const count = note.value.trim() ? note.value.trim().split(/\s+/).length : 0;
  wordCount.textContent = `${count} ${count === 1 ? 'word' : 'words'}`;
}

function saveNote() {
  saveState.classList.add('saving');
  saveState.innerHTML = '<i></i> Saving locally';
  window.clearTimeout(saveTimer);
  saveTimer = window.setTimeout(() => {
    localStorage.setItem('testflight-founder-note', note.value);
    saveState.classList.remove('saving');
    saveState.innerHTML = '<i></i> Saved in this browser';
  }, 420);
}

function renderQuestion() {
  const question = questions[questionIndex];
  document.querySelector('#question-number').textContent = String(questionIndex + 1).padStart(2, '0');
  document.querySelector('#source-quote').textContent = question.quote;
  document.querySelector('#question-text').textContent = question.text;
  document.querySelector('#clarify-answer').value = '';
}

function renderEvidence(key) {
  const item = evidence[key];
  document.querySelector('#evidence-title').textContent = item.title;
  document.querySelector('#evidence-quotes').innerHTML = item.quotes.map(([quote, source]) => `<blockquote>${quote}<cite>${source}</cite></blockquote>`).join('');
}

document.querySelectorAll('.view-switch').forEach((button) => button.addEventListener('click', () => switchView(button.dataset.view)));

note.value = localStorage.getItem('testflight-founder-note') || '';
updateWordCount();
note.addEventListener('input', () => { updateWordCount(); saveNote(); });

document.querySelectorAll('.prompt').forEach((button) => button.addEventListener('click', () => {
  const separator = note.value.trim() ? '\n\n' : '';
  note.value += `${separator}${button.dataset.prompt} `;
  note.focus();
  note.setSelectionRange(note.value.length, note.value.length);
  updateWordCount();
  saveNote();
}));

window.setInterval(() => { sessionSeconds += 1; sessionTime.textContent = formatTime(sessionSeconds); }, 1000);

recordButton.addEventListener('click', () => {
  const recording = recordButton.classList.toggle('recording');
  recordButton.setAttribute('aria-pressed', String(recording));
  if (recording) {
    recordingSeconds = 0;
    recordTime.textContent = '00:00';
    recordingTimer = window.setInterval(() => { recordingSeconds += 1; recordTime.textContent = formatTime(recordingSeconds); }, 1000);
    showToast('Voice-note interaction simulated. No audio is recorded in this prototype.');
  } else {
    window.clearInterval(recordingTimer);
    recordTime.textContent = 'voice note';
    if (recordingSeconds > 0) {
      attachmentList.insertAdjacentHTML('beforeend', `<span class="file-chip">Voice note · ${formatTime(recordingSeconds)}</span>`);
    }
  }
});

document.querySelector('#attachment-button').addEventListener('click', () => attachmentInput.click());
attachmentInput.addEventListener('change', () => {
  [...attachmentInput.files].forEach((file) => attachmentList.insertAdjacentHTML('beforeend', `<span class="file-chip" title="${file.name}">${file.name}</span>`));
  showToast(`${attachmentInput.files.length} ${attachmentInput.files.length === 1 ? 'attachment' : 'attachments'} added to the prototype.`);
});

document.querySelector('#finish-button').addEventListener('click', () => {
  showToast('Day one saved. Moving forward only for this prototype.');
  window.setTimeout(() => switchView('clarify'), 500);
});

document.querySelector('#next-question').addEventListener('click', () => {
  questionIndex = (questionIndex + 1) % questions.length;
  renderQuestion();
  showToast(questionIndex === 0 ? 'Clarification set complete.' : 'Answer kept. Here is the next distinction.');
});

document.querySelector('#skip-question').addEventListener('click', () => {
  questionIndex = (questionIndex + 1) % questions.length;
  renderQuestion();
  showToast('“I don’t know” kept as useful information.');
});

document.querySelector('#voice-answer').addEventListener('click', () => showToast('Voice answering would use the same transcription adapter as notebook recordings.'));
document.querySelector('#source-link').addEventListener('click', () => showToast('Source view: Day one · written note · exact excerpt preserved.'));

document.querySelectorAll('.world-fragment').forEach((button) => button.addEventListener('click', () => {
  document.querySelectorAll('.world-fragment').forEach((fragment) => fragment.classList.remove('selected'));
  button.classList.add('selected');
  renderEvidence(button.dataset.evidence);
  document.querySelector('#evidence-drawer').scrollIntoView({ behavior: 'smooth', block: 'nearest' });
}));

const privacyDialog = document.querySelector('#privacy-dialog');
document.querySelector('#privacy-button').addEventListener('click', () => privacyDialog.showModal());
document.querySelector('#dialog-close').addEventListener('click', () => privacyDialog.close());
privacyDialog.addEventListener('click', (event) => { if (event.target === privacyDialog) privacyDialog.close(); });
document.querySelector('.review-action').addEventListener('click', () => showToast('The production review workspace will open the full evidence and decision record.'));

renderQuestion();
