document.addEventListener('DOMContentLoaded', () => {
    const menuManager = {
        // State
        selectedHall: 'Dana',
        selectedDate: new Date().toISOString().split('T')[0],
        selectedMealPeriod: 'all',
        dietaryFilters: new Set(),
        searchTerm: '',
        searchDebounceTimer: null,


        // DOM Elements
        init() {
            this.menuContainer = document.getElementById('menu-container');
            this.loadingSpinner = document.getElementById('loading-spinner');
            this.errorMessage = document.getElementById('error-message');
            this.initializeEventListeners();
            this.loadMenu();
        },

        initializeEventListeners() {
            // Dining Hall buttons
            document.querySelectorAll('[data-hall]').forEach(button => {
                button.addEventListener('click', (e) => {
                    this.selectedHall = e.target.dataset.hall;
                    this.updateActiveButton(e.target, '[data-hall]');
                    this.loadMenu();
                });
            });

            // Date picker
            const datePicker = document.getElementById('date-picker');
            if (datePicker) {
                datePicker.value = this.selectedDate;
                datePicker.addEventListener('change', (e) => {
                    this.selectedDate = e.target.value;
                    this.loadMenu();
                });
            }

            // Meal period buttons
            document.querySelectorAll('[data-period]').forEach(button => {
                button.addEventListener('click', (e) => {
                    this.selectedMealPeriod = e.target.dataset.period;
                    this.updateActiveButton(e.target, '[data-period]');
                    this.filterCurrentMenu();
                });
            });

            // Dietary filters
            document.querySelectorAll('.dietary-filter').forEach(checkbox => {
                checkbox.addEventListener('change', (e) => {
                    if (e.target.checked) {
                        this.dietaryFilters.add(e.target.value);
                    } else {
                        this.dietaryFilters.delete(e.target.value);
                    }
                    this.filterCurrentMenu();
                });
            });
            
            const searchInput = document.getElementById('menu-search');
            if (searchInput) {
                searchInput.addEventListener('input', (e) => {
                    // Clear existing timer
                    if (this.searchDebounceTimer) {
                        clearTimeout(this.searchDebounceTimer);
                    }

                    // Set new timer to debounce search
                    this.searchDebounceTimer = setTimeout(() => {
                        this.searchTerm = e.target.value.toLowerCase().trim();
                        this.filterCurrentMenu();
                    }, 300);
                });
            }
        },

        updateActiveButton(activeButton, selector) {
            document.querySelectorAll(selector).forEach(button => {
                button.classList.remove('active');
            });
            activeButton.classList.add('active');
        },

        async loadMenu() {
            try {
                // Show loading state only for initial load or dining hall/date changes
                this.showLoading();

                const response = await fetch(`/api/menu/current?dining_hall=${encodeURIComponent(this.selectedHall)}&date=${encodeURIComponent(this.selectedDate)}`);
                const data = await response.json();

                if (data.status === 'success' && data.menu) {
                    this.currentMenuData = data.menu;
                    this.filterCurrentMenu();
                    // Hide loading state after menu is rendered
                    this.hideLoading();
                } else {
                    throw new Error(data.error || 'Failed to load menu data');
                }
            } catch (error) {
                console.error('Error loading menu:', error);
                this.showError(error.message || 'Failed to load menu');
            }
        },

        filterCurrentMenu() {
            if (!this.currentMenuData) {
                this.showError('No menu data available');
                return;
            }

            // No loading spinner for filtering operations
            this.menuContainer.innerHTML = '';
            const periods = this.selectedMealPeriod === 'all' 
                ? Object.keys(this.currentMenuData)
                : [this.selectedMealPeriod];

                periods.forEach(period => {
                    if (this.currentMenuData[period]) {
                        // First apply dietary filters
                        let items = this.filterItems(this.currentMenuData[period]);
                        
                        // Then apply search filter if there's a search term
                        if (this.searchTerm) {
                            items = this.filterBySearch(items);
                        }
    
                        if (items.length > 0) {
                            this.displayMealPeriod(period, items);
                        }
                    }
                });

            if (this.menuContainer.children.length === 0) {
                this.menuContainer.innerHTML = `
                    <div class="no-results">
                        No menu items found matching your criteria
                    </div>`;
            }
        
            // Make sure menu container is visible after filtering
            this.menuContainer.classList.remove('hidden');
            if (this.loadingSpinner) {
                this.loadingSpinner.classList.add('hidden');
            }
        },

        filterBySearch(items) {
            return items.filter(item => {
                const searchFields = [
                    item.name,
                    item.description,
                    item.station,
                    ...(item.dietary_flags || [])
                ].map(field => (field || '').toLowerCase());

                return searchFields.some(field => field.includes(this.searchTerm));
            });
        },

        filterItems(items) {
            if (this.dietaryFilters.size === 0) return items;

            return items.filter(item => {
                return Array.from(this.dietaryFilters).every(filter => 
                    item.dietary_flags.includes(filter)
                );
            });
        },

        displayMealPeriod(periodName, items) {
            const section = document.createElement('div');
            section.className = 'meal-section';
            
            section.innerHTML = `
                <h2>${periodName}</h2>
                ${this.createStationsHtml(this.groupByStation(items))}
            `;
            
            this.menuContainer.appendChild(section);
        },

        groupByStation(items) {
            return items.reduce((grouped, item) => {
                const station = item.station || 'Other';
                if (!grouped[station]) {
                    grouped[station] = [];
                }
                grouped[station].push(item);
                return grouped;
            }, {});
        },

        createStationsHtml(stations) {
            return Object.entries(stations).map(([stationName, items]) => `
                <div class="station-section">
                    <h3>${stationName}</h3>
                    <div class="menu-items-grid">
                        ${items.map(item => this.createItemHtml(item)).join('')}
                    </div>
                </div>
            `).join('');
        },

        createItemHtml(item) {
            return `
                <div class="menu-item">
                    <h4>${item.name}</h4>
                    ${item.description ? `<p>${item.description}</p>` : ''}
                    ${this.createDietaryFlagsHtml(item.dietary_flags)}
                    ${this.createNutritionHtml(item.nutrition)}
                </div>
            `;
        },

        createDietaryFlagsHtml(flags) {
            if (!flags || flags.length === 0) return '';
            
            return `
                <div class="dietary-flags">
                    ${flags.map(flag => `
                        <span class="dietary-badge">${flag}</span>
                    `).join('')}
                </div>
            `;
        },

        createNutritionHtml(nutrition) {
            if (!nutrition || !nutrition.calories) return '';
            
            return `
                <div class="nutrition-info">
                    ${nutrition.calories} calories
                </div>
            `;
        },

        showLoading() {
            if (this.loadingSpinner) {
                this.loadingSpinner.classList.remove('hidden');
            }
            if (this.menuContainer) {
                this.menuContainer.classList.add('hidden');
            }
            if (this.errorMessage) {
                this.errorMessage.classList.add('hidden');
            }
        },

        hideLoading() {
            if (this.loadingSpinner) {
                this.loadingSpinner.classList.add('hidden');
            }
            if (this.menuContainer) {
                this.menuContainer.classList.remove('hidden');
            }
        },

        showError(message) {
            if (this.loadingSpinner) {
                this.loadingSpinner.classList.add('hidden');
            }
            if (this.errorMessage) {
                this.errorMessage.textContent = message;
                this.errorMessage.classList.remove('hidden');
            }
            if (this.menuContainer) {
                this.menuContainer.classList.add('hidden');
            }
        }
    };

    // Initialize the menu manager
    menuManager.init();
});