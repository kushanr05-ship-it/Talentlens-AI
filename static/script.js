document.addEventListener('DOMContentLoaded', () => {
    const form = document.getElementById('form');
    const resumeInput = document.getElementById('resumeInput');
    const fileNameDisplay = document.getElementById('fileNameDisplay');
    const submitBtn = document.getElementById('submitBtn');
    const btnText = document.getElementById('btnText');
    const spinner = document.getElementById('spinner');
    const reportContent = document.getElementById('reportContent');
    const uploadWrapper = document.getElementById('uploadWrapper');
    const printBtn = document.getElementById('printBtn');
    const uploadPage = document.getElementById('uploadPage');
    const reportPage = document.getElementById('reportPage');
    const candidatesPage = document.getElementById('candidatesPage');
    const navDashboardBtn = document.getElementById('navDashboardBtn');
    const navCandidatesBtn = document.getElementById('navCandidatesBtn');
    const refreshCandidatesBtn = document.getElementById('refreshCandidatesBtn');
    const downloadReportBtn = document.getElementById('downloadReportBtn');
    const candidatesList = document.getElementById('candidatesList');
    
    const backBtn = document.getElementById('backBtn');
    const upgradeBtn = document.getElementById('upgradeBtn');
    const upgradeBtnText = upgradeBtn.querySelector('.upgrade-btn-text');
    const upgradeSpinner = document.getElementById('upgradeSpinner');
    
    // Chat DOM Elements
    const chatForm = document.getElementById('chatForm');
    const chatInput = document.getElementById('chatInput');
    const chatBox = document.getElementById('chatBox');
    const chatSendBtn = document.getElementById('chatSendBtn');
    
    let currentResumeText = "";

    // Handle file selection UI details
    resumeInput.addEventListener('change', (e) => {
        if (e.target.files.length > 0) {
            let isValid = true;
            for(let i=0; i<e.target.files.length; i++){
                if(!e.target.files[i].name.toLowerCase().endsWith('.pdf')){
                   isValid = false; 
                }
            }
            
            if (isValid) {
                if (e.target.files.length === 1) {
                    fileNameDisplay.textContent = e.target.files[0].name;
                } else {
                    fileNameDisplay.textContent = `${e.target.files.length} resumes selected for batch.`;
                }
                fileNameDisplay.style.color = '#131b2e';
                fileNameDisplay.style.fontWeight = 'bold';
                uploadWrapper.style.borderColor = '#392cc1';
                
                // Subtle bounce animation on file select
                uploadWrapper.style.transform = 'scale(1.03)';
                setTimeout(() => {
                    uploadWrapper.style.transform = 'scale(1)';
                }, 250);
            } else {
                fileNameDisplay.textContent = 'Invalid file. Please select a PDF.';
                fileNameDisplay.style.color = '#ba1a1a';
                uploadWrapper.style.borderColor = '#ba1a1a';
                resumeInput.value = '';
            }
        } else {
            fileNameDisplay.textContent = 'Click to browse or drag & drop';
            fileNameDisplay.style.color = '';
            fileNameDisplay.style.fontWeight = 'normal';
            uploadWrapper.style.borderColor = '';
        }
    });

    // Trigger hidden file input when clicking wrapper
    uploadWrapper.addEventListener('click', (e) => {
        // Prevent infinite click loop if the input itself fired the click
        if (e.target.id !== 'resumeInput') {
            resumeInput.click();
        }
    });

    // Handle drag and drop styling
    uploadWrapper.addEventListener('dragover', (e) => {
        e.preventDefault();
        uploadWrapper.classList.add('dragover');
    });
    
    uploadWrapper.addEventListener('dragleave', () => {
        uploadWrapper.classList.remove('dragover');
    });
    
    uploadWrapper.addEventListener('drop', (e) => {
        e.preventDefault();
        uploadWrapper.classList.remove('dragover');
        if (e.dataTransfer.files.length > 0) {
            // Check if file is PDF
            if (e.dataTransfer.files[0].type !== 'application/pdf' && !e.dataTransfer.files[0].name.toLowerCase().endsWith('.pdf')) {
                alert("Please drop a valid .pdf document.");
                return;
            }
            resumeInput.files = e.dataTransfer.files;
            
            // Trigger change event manually
            const event = new Event('change');
            resumeInput.dispatchEvent(event);
        }
    });

    // Handle printing the report
    if (printBtn) {
        printBtn.addEventListener('click', () => {
            window.print();
        });
    }

    // Handle back button for new analysis
    backBtn.addEventListener('click', () => {
        reportPage.classList.add('hidden');
        uploadPage.classList.remove('hidden');
        candidatesPage.classList.add('hidden');
        reportContent.innerHTML = '';
        currentResumeText = "";
        
        // Reset Chat
        chatBox.innerHTML = `
            <div class="chat-message ai-message">
                <div class="message-content">Hello! I've analyzed the resume. What specific questions do you have about this candidate?</div>
            </div>`;
            
        form.reset();
        fileNameDisplay.textContent = 'Drag and drop files here';
        fileNameDisplay.style.color = '';
        fileNameDisplay.style.fontWeight = 'bold';
        uploadWrapper.style.borderColor = '';
        window.scrollTo({ top: 0, behavior: 'smooth' });
    });

    // Handle form submission
    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        const jobDescription = document.getElementById('jobDescription').value;
        const resumeFile = resumeInput.files[0];
        
        if (!jobDescription || !resumeFile) {
            alert('Please provide both a job description and a resume file.');
            return;
        }
        
        // Show loading state
        spinner.style.display = 'inline-block';
        submitBtn.disabled = true;
        
        const loadingTexts = [
            'Extracting text from PDF...',
            'Connecting to Gensara AI...',
            'Cross-referencing requirements...',
            'Scoring candidate match...',
            'Generating final markdown report... (almost done)'
        ];
        let textIndex = 0;
        btnText.textContent = loadingTexts[0];
        
        const textInterval = setInterval(() => {
            textIndex = Math.min(textIndex + 1, loadingTexts.length - 1);
            btnText.textContent = loadingTexts[textIndex];
        }, 5000); // update every 5 seconds
        
        // Prepare FormData for the backend
        const formData = new FormData();
        formData.append('job_description', jobDescription);
        
        // Append all selected files to the Form Data array
        for(let i=0; i<resumeInput.files.length; i++) {
            formData.append('resumes', resumeInput.files[i]);
        }
        
        try {
            const response = await fetch('/api/analyze', {
                method: 'POST',
                body: formData
            });
            
            const data = await response.json();
            
            if (response.ok) {
                // Strip markdown fences
                let rawMarkdown = data.report.replace(/^```(?:markdown)?\s*/i, '').replace(/\s*```$/i, '');
                
                // Parse markdown into HTML and display it
                reportContent.innerHTML = marked.parse(rawMarkdown);
                currentResumeText = data.resume_text; // Save for chat context
                
                // Switch pages
                uploadPage.classList.add('hidden');
                reportPage.classList.remove('hidden');
                
                // Add a small delay for animation, then scroll to top
                setTimeout(() => {
                    window.scrollTo({ top: 0, behavior: 'smooth' });
                }, 100);
            } else {
                throw new Error(data.detail || 'An error occurred during analysis.');
            }
        } catch (error) {
            alert('Error: ' + error.message);
        } finally {
            clearInterval(textInterval);
            // Restore button state
            btnText.textContent = 'Analyze Candidate Match';
            spinner.style.display = 'none';
            submitBtn.disabled = false;
        }
    });

    // Handle Upgrade File request
    upgradeBtn.addEventListener('click', async () => {
        const jobDescription = document.getElementById('jobDescription').value;
        const resumeFile = resumeInput.files[0];
        
        if (!resumeFile || !jobDescription) return;
        
        upgradeBtnText.textContent = 'Upgrading Resume...';
        upgradeSpinner.style.display = 'inline-block';
        upgradeBtn.disabled = true;
        
        const formData = new FormData();
        formData.append('job_description', jobDescription);
        formData.append('resume', resumeFile);
        
        try {
            const response = await fetch('/api/upgrade', {
                method: 'POST',
                body: formData
            });
            const data = await response.json();
            
            if (response.ok) {
                // Strip markdown fences
                let rawMarkdown = data.report.replace(/^```(?:markdown)?\s*/i, '').replace(/\s*```$/i, '');
                
                // Change the report content to the upgraded version
                reportContent.innerHTML = '<h2 style="color:var(--blob-1); margin-bottom:20px;">✨ Your Auto-Upgraded Resume</h2>' + marked.parse(rawMarkdown);
                window.scrollTo({ top: 0, behavior: 'smooth' });
            } else {
                throw new Error(data.detail || 'An error occurred during upgrade.');
            }
        } catch (error) {
            alert('Upgrade Error: ' + error.message);
        } finally {
            upgradeBtnText.textContent = 'Upgrade Resume with AI';
            upgradeSpinner.style.display = 'none';
            upgradeBtn.disabled = false;
        }
    });

    // Chat Functionality Helpers
    function addChatMessage(text, sender) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `chat-message ${sender}-message`;
        messageDiv.innerHTML = `<div class="message-content">${marked.parse(text)}</div>`;
        chatBox.appendChild(messageDiv);
        chatBox.scrollTop = chatBox.scrollHeight;
    }

    function addChatTypingIndicator() {
        const id = 'typing-' + Date.now();
        const indicator = document.createElement('div');
        indicator.className = 'chat-message ai-message';
        indicator.id = id;
        indicator.innerHTML = `
            <div class="message-content typing-indicator">
                <div class="typing-dot"></div>
                <div class="typing-dot"></div>
                <div class="typing-dot"></div>
            </div>`;
        chatBox.appendChild(indicator);
        chatBox.scrollTop = chatBox.scrollHeight;
        return id;
    }

    // Handle Chat Form Submission
    chatForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const question = chatInput.value.trim();
        if (!question || !currentResumeText) return;

        addChatMessage(question, 'user');
        chatInput.value = '';
        chatInput.disabled = true;
        chatSendBtn.disabled = true;

        const typingId = addChatTypingIndicator();

        try {
            const response = await fetch('/api/chat', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    resume_text: currentResumeText,
                    question: question
                })
            });
            
            const data = await response.json();
            document.getElementById(typingId)?.remove();
            
            if (response.ok) {
                addChatMessage(data.answer, 'ai');
            } else {
                addChatMessage("Oops, I encountered an error. Backend issue.", 'ai');
            }
        } catch (error) {
            document.getElementById(typingId)?.remove();
            addChatMessage("Oops, connection failed. Please try again.", 'ai');
        } finally {
            chatInput.disabled = false;
            chatSendBtn.disabled = false;
            chatInput.focus();
        }
    });

    // ============================================
    // CANDIDATES DASHBOARD LOGIC
    // ============================================
    
    function showDashboard() {
        uploadPage.classList.remove('hidden');
        reportPage.classList.add('hidden');
        candidatesPage.classList.add('hidden');
    }
    
    function showCandidates() {
        uploadPage.classList.add('hidden');
        reportPage.classList.add('hidden');
        candidatesPage.classList.remove('hidden');
        fetchCandidatesHistory();
    }
    
    navDashboardBtn.addEventListener('click', showDashboard);
    navCandidatesBtn.addEventListener('click', showCandidates);
    refreshCandidatesBtn.addEventListener('click', fetchCandidatesHistory);
    
    if (downloadReportBtn) {
        downloadReportBtn.addEventListener('click', () => {
            const filenameObj = fileNameDisplay.textContent.replace(".pdf", "");
            const reportTxt = reportContent.innerText;
            
            // Trigger download via Blob as standard Text
            const blob = new Blob([reportTxt], { type: 'text/plain;charset=utf-8;' });
            const url = URL.createObjectURL(blob);
            const link = document.createElement('a');
            link.setAttribute('href', url);
            link.setAttribute('download', `${filenameObj}_TalentLens.txt`);
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
        });
    }
    
    async function fetchCandidatesHistory() {
        candidatesList.innerHTML = `
            <div class="p-8 text-center text-secondary w-full">
                <span class="spinner inline-block" style="border-top-color: #392cc1; border-width: 2px; width: 24px; height: 24px;"></span>
                <p class="mt-4">Loading history...</p>
            </div>
        `;
        
        try {
            const response = await fetch('/api/candidates');
            if(!response.ok) throw new Error("Failed to fetch database records");
            const data = await response.json();
            
            candidatesList.innerHTML = '';
            
            if(data.length === 0) {
                candidatesList.innerHTML = `<div class="p-8 text-center text-secondary">No candidates processed yet.</div>`;
                return;
            }
            
            data.forEach(candidate => {
                const date = new Date(candidate.created_at).toLocaleString();
                const card = document.createElement('div');
                card.className = "p-6 flex flex-col md:flex-row justify-between items-start md:items-center gap-4 hover:bg-surface-container-low transition-colors";
                card.innerHTML = `
                    <div class="flex-1">
                        <h4 class="font-bold text-on-surface mb-1">${candidate.filename}</h4>
                        <p class="text-xs text-secondary truncate max-w-sm">Evaluated on ${date}</p>
                    </div>
                    <button class="review-btn bg-primary text-white px-4 py-2 rounded-xl text-sm font-bold active:scale-95 transition-transform">
                        Review Report
                    </button>
                `;
                
                const btn = card.querySelector('.review-btn');
                btn.addEventListener('click', () => {
                    // 1. Map Candidate attributes to current session memory
                    currentResumeText = candidate.resume_text;
                    
                    // 2. Parse Markdown
                    reportContent.innerHTML = marked.parse(candidate.report);
                    
                    // 3. Reset Chat Context intelligently
                    chatBox.innerHTML = `
                        <div class="chat-message ai-message">
                            <div class="message-content">Hello! I have recalled the historical data for <b>${candidate.filename}</b> from the database. What specific questions do you have about this analysis?</div>
                        </div>`;
                        
                    // 4. Switch screens back to the active report view
                    candidatesPage.classList.add('hidden');
                    uploadPage.classList.add('hidden');
                    reportPage.classList.remove('hidden');
                    
                    // 5. Scroll to top
                    window.scrollTo({ top: 0, behavior: 'smooth' });
                });
                
                candidatesList.appendChild(card);
            });
            
        } catch(e) {
            console.error(e);
            candidatesList.innerHTML = `<div class="p-8 text-center text-error border border-error-container bg-error-container/20 rounded-xl m-4">Failed to load history.</div>`;
        }
    }

});
