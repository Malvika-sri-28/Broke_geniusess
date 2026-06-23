document.addEventListener('DOMContentLoaded', function () {
    // 1. Dynamic University "Other" Field Display
    const uniSelect = document.getElementById('university_select');
    const uniOtherContainer = document.getElementById('university_other_container');
    const uniOtherInput = document.getElementById('university_other');

    if (uniSelect && uniOtherContainer) {
        function toggleUniOther() {
            if (uniSelect.value === 'Other') {
                uniOtherContainer.classList.remove('d-none');
                uniOtherInput.setAttribute('required', 'required');
            } else {
                uniOtherContainer.classList.add('d-none');
                uniOtherInput.removeAttribute('required');
            }
        }
        
        uniSelect.addEventListener('change', toggleUniOther);
        toggleUniOther(); // run initially on page load
    }

    // 2. Interactive Star Rating Selector
    const starSelector = document.getElementById('interactive-star-selector');
    const ratingInput = document.getElementById('rating-input');
    
    if (starSelector && ratingInput) {
        const stars = starSelector.querySelectorAll('.bi');
        
        stars.forEach(star => {
            star.addEventListener('click', function() {
                const val = parseInt(this.getAttribute('data-value'));
                ratingInput.value = val;
                
                // Highlight active stars
                stars.forEach((s, idx) => {
                    if (idx < val) {
                        s.classList.remove('bi-star');
                        s.classList.add('bi-star-fill');
                    } else {
                        s.classList.remove('bi-star-fill');
                        s.classList.add('bi-star');
                    }
                });
            });
            
            // Hover preview support
            star.addEventListener('mouseenter', function() {
                const val = parseInt(this.getAttribute('data-value'));
                stars.forEach((s, idx) => {
                    if (idx < val) {
                        s.classList.remove('bi-star');
                        s.classList.add('bi-star-fill');
                    } else {
                        s.classList.remove('bi-star-fill');
                        s.classList.add('bi-star');
                    }
                });
            });
        });
        
        // Reset to selected rating when mouse leaves container
        starSelector.addEventListener('mouseleave', function() {
            const val = parseInt(ratingInput.value) || 0;
            stars.forEach((s, idx) => {
                if (idx < val) {
                    s.classList.remove('bi-star');
                    s.classList.add('bi-star-fill');
                } else {
                    s.classList.remove('bi-star-fill');
                    s.classList.add('bi-star');
                }
            });
        });
    }

    // 3. Image File Upload Preview (Profiles & Services)
    const fileInput = document.querySelector('.image-preview-input');
    const imagePreview = document.querySelector('.image-preview-target');
    
    if (fileInput && imagePreview) {
        fileInput.addEventListener('change', function() {
            const file = this.files[0];
            if (file) {
                const reader = new FileReader();
                reader.onload = function(e) {
                    imagePreview.setAttribute('src', e.target.result);
                }
                reader.readAsDataURL(file);
            }
        });
    }

    // 4. Custom Delete Confirmations
    const deleteForms = document.querySelectorAll('.delete-confirm-form');
    deleteForms.forEach(form => {
        form.addEventListener('submit', function(e) {
            const itemType = this.getAttribute('data-item-type') || 'item';
            const confirmed = confirm(`Are you sure you want to delete this ${itemType}? This action cannot be undone.`);
            if (!confirmed) {
                e.preventDefault();
            }
        });
    });

    // 5. Predefined Avatar Selector logic
    const avatarCards = document.querySelectorAll('.avatar-select-card');
    const selectedAvatarInput = document.getElementById('selected_avatar');
    
    if (avatarCards && selectedAvatarInput) {
        avatarCards.forEach(card => {
            card.addEventListener('click', function() {
                // Remove active class from all other avatar options
                avatarCards.forEach(c => c.classList.remove('active'));
                
                // Add active class to this card
                this.classList.add('active');
                
                // Set hidden input value
                const avatarFilename = this.getAttribute('data-avatar');
                selectedAvatarInput.value = avatarFilename;
                
                // Update target preview image
                if (imagePreview) {
                    const relativePath = '/static/avatars/' + avatarFilename;
                    imagePreview.setAttribute('src', relativePath);
                }
                
                // Reset file upload input so it doesn't conflict
                if (fileInput) {
                    fileInput.value = '';
                }
            });
        });
    }
    
    // Clear avatar selector selection if user uploads a custom file instead
    if (fileInput && avatarCards && selectedAvatarInput) {
        fileInput.addEventListener('change', function() {
            if (this.files && this.files[0]) {
                avatarCards.forEach(c => c.classList.remove('active'));
                selectedAvatarInput.value = '';
            }
        });
    }

    // 6. Floating AI Assistant Chatbot
    const aiChatFab = document.getElementById('ai-chat-fab');
    const aiChatPanel = document.getElementById('ai-chat-panel');
    const aiChatClose = document.getElementById('ai-chat-close');
    const aiChatForm = document.getElementById('ai-chat-form');
    const aiChatInput = document.getElementById('ai-chat-input');
    const aiMessagesContainer = document.getElementById('ai-chat-messages');
    const aiChips = document.querySelectorAll('.ai-chip');

    // Get CSRF Token from meta tag
    const csrfMeta = document.querySelector('meta[name="csrf-token"]');
    const csrfToken = csrfMeta ? csrfMeta.getAttribute('content') : '';

    function formatResponseText(text) {
        // Escape HTML to prevent XSS
        let escaped = text
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;")
            .replace(/"/g, "&quot;")
            .replace(/'/g, "&#039;");
        
        // Convert markdown links: [text](url) -> <a href="url">text</a>
        escaped = escaped.replace(/\[([^\]]+)\]\(([^)]+)\)/g, function(match, p1, p2) {
            return `<a href="${p2}">${p1}</a>`;
        });
        
        // Convert formatting
        escaped = escaped.replace(/\n/g, '<br>');
        escaped = escaped.replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>');
        escaped = escaped.replace(/\*([^*]+)\*/g, '<em>$1</em>');
        escaped = escaped.replace(/`([^`]+)`/g, '<code>$1</code>');
        return escaped;
    }

    function addChatMessage(sender, text) {
        if (!aiMessagesContainer) return;
        const messageDiv = document.createElement('div');
        messageDiv.classList.add('ai-message', sender === 'ai' ? 'incoming' : 'outgoing');
        messageDiv.innerHTML = sender === 'ai' ? formatResponseText(text) : text.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
        aiMessagesContainer.appendChild(messageDiv);
        aiMessagesContainer.scrollTop = aiMessagesContainer.scrollHeight;
    }

    async function sendQueryToAI(messageText) {
        if (!messageText.trim()) return;
        
        // Add user message to UI
        addChatMessage('user', messageText);
        if (aiChatInput) aiChatInput.value = '';

        // Add loading state bubble
        const loadingDiv = document.createElement('div');
        loadingDiv.classList.add('ai-message', 'incoming');
        loadingDiv.innerHTML = `<div class="d-flex align-items-center gap-2"><div class="spinner-border spinner-border-sm text-primary" role="status" style="width: 0.8rem; height: 0.8rem;"></div><span>Thinking...</span></div>`;
        if (aiMessagesContainer) {
            aiMessagesContainer.appendChild(loadingDiv);
            aiMessagesContainer.scrollTop = aiMessagesContainer.scrollHeight;
        }

        try {
            const response = await fetch('/ai/chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': csrfToken
                },
                body: JSON.stringify({ message: messageText })
            });
            
            // Remove loading bubble
            loadingDiv.remove();

            if (response.ok) {
                const data = await response.json();
                addChatMessage('ai', data.response || "Sorry, I couldn't get a response.");
            } else {
                addChatMessage('ai', "⚠️ Error: Failed to communicate with AI server.");
            }
        } catch (error) {
            loadingDiv.remove();
            console.error('AI chat error:', error);
            addChatMessage('ai', "⚠️ Network Error: Please check your connection.");
        }
    }

    if (aiChatFab && aiChatPanel && aiMessagesContainer) {
        aiChatFab.addEventListener('click', function(e) {
            e.stopPropagation();
            if (aiChatPanel.classList.contains('show')) {
                aiChatPanel.classList.remove('show');
            } else {
                aiChatPanel.classList.add('show');
                aiMessagesContainer.scrollTop = aiMessagesContainer.scrollHeight;
                if (aiChatInput) aiChatInput.focus();
            }
        });

        if (aiChatClose) {
            aiChatClose.addEventListener('click', function(e) {
                e.stopPropagation();
                aiChatPanel.classList.remove('show');
            });
        }

        // Close chat when clicking outside
        document.addEventListener('click', function(e) {
            if (!aiChatPanel.contains(e.target) && e.target !== aiChatFab && !aiChatFab.contains(e.target)) {
                aiChatPanel.classList.remove('show');
            }
        });

        if (aiChatForm) {
            aiChatForm.addEventListener('submit', function(e) {
                e.preventDefault();
                if (aiChatInput) {
                    const message = aiChatInput.value.trim();
                    if (message) {
                        sendQueryToAI(message);
                    }
                }
            });
        }

        // Chip Clicks
        aiChips.forEach(chip => {
            chip.addEventListener('click', function() {
                const query = this.getAttribute('data-query');
                if (query) {
                    sendQueryToAI(query);
                }
            });
        });
    }

    // 7. AI Auto-Generate Description handler
    const aiGenBtn = document.getElementById('ai-gen-description-btn');
    const titleInput = document.getElementById('title');
    const descTextarea = document.getElementById('description');
    const aiGenSpinner = document.getElementById('ai-gen-spinner');
    const aiGenIcon = document.getElementById('ai-gen-icon');

    if (aiGenBtn && titleInput && descTextarea) {
        aiGenBtn.addEventListener('click', async function() {
            const titleValue = titleInput.value.trim();
            if (!titleValue) {
                alert("Please enter a Service Title first so the AI can generate a description based on it.");
                titleInput.focus();
                return;
            }

            // Show loader
            if (aiGenSpinner) aiGenSpinner.style.display = 'inline-block';
            if (aiGenIcon) aiGenIcon.style.display = 'none';
            aiGenBtn.style.pointerEvents = 'none';
            aiGenBtn.style.opacity = '0.7';

            try {
                const response = await fetch('/ai/generate-description', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': csrfToken
                    },
                    body: JSON.stringify({ title: titleValue })
                });

                if (response.ok) {
                    const data = await response.json();
                    if (data.description) {
                        descTextarea.value = data.description;
                    } else {
                        alert("Could not generate description. Please try again.");
                    }
                } else {
                    alert("Error communicating with AI endpoint.");
                }
            } catch (error) {
                console.error("AI Generate Description error:", error);
                alert("Network error: Please check your connection.");
            } finally {
                // Hide loader
                if (aiGenSpinner) aiGenSpinner.style.display = 'none';
                if (aiGenIcon) aiGenIcon.style.display = 'inline-block';
                aiGenBtn.style.pointerEvents = 'auto';
                aiGenBtn.style.opacity = '1';
            }
        });
    }

    // 8. Auto-popup Jokes
    const jokePopup = document.getElementById('ai-joke-popup');
    const jokePopupBody = document.getElementById('ai-joke-popup-body');
    const jokePopupClose = document.getElementById('ai-joke-popup-close');

    const popupJokes = [
        "Why do student programmers prefer dark mode? Because light attracts bugs!",
        "What's a broke student's favorite matrix? The Identity Matrix—because it has all the ones, just like their wallet.",
        "Why was the student's database project crying? Because it had too many relations, and none of them worked.",
        "How do students study for exams? 1% studying, 99% calculating the minimum score they need to pass.",
        "Student budget: 'I can buy this book, or I can eat for the next three weeks. Decisions, decisions.'",
        "Why did the computer science student fail their exam? They kept looking for index 1, but the arrays started at 0.",
        "Professor: 'Your assignment must be original.' Student: *Right click -> Inspect -> Edit as HTML*",
        "My university is so exclusive, even my GPA isn't allowed to go above 2.0.",
        "How many college students does it take to change a lightbulb? One, but it will be done 10 minutes before the deadline.",
        "There are 10 types of students: those who understand binary, and those who don't.",
        "I told my professor that my dog ate my coding assignment. He said, 'That's impossible, it was on GitHub.' He said, 'Well, he took a byte out of it!'"
    ];

    function showRandomPopupJoke() {
        if (!jokePopup || !jokePopupBody) return;
        // Don't show if the chatbot panel is open
        if (aiChatPanel && aiChatPanel.classList.contains('show')) return;
        
        const idx = Math.floor(Math.random() * popupJokes.length);
        jokePopupBody.textContent = popupJokes[idx];
        jokePopup.classList.add('show');

        // Auto hide after 12 seconds
        setTimeout(() => {
            jokePopup.classList.remove('show');
        }, 12000);
    }

    if (jokePopup) {
        if (jokePopupClose) {
            jokePopupClose.addEventListener('click', function(e) {
                e.stopPropagation();
                jokePopup.classList.remove('show');
            });
        }

        // Close popup if user clicks chatbot FAB
        if (aiChatFab) {
            aiChatFab.addEventListener('click', function() {
                jokePopup.classList.remove('show');
            });
        }

        // Trigger first joke after 6 seconds
        setTimeout(showRandomPopupJoke, 6000);

        // Schedule random jokes every 45 seconds
        setInterval(function() {
            showRandomPopupJoke();
        }, 45000);
    }
});
