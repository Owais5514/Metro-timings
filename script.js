// Mobile Navigation Toggle
document.addEventListener('DOMContentLoaded', function() {
    const hamburger = document.querySelector('.hamburger');
    const navMenu = document.querySelector('.nav-menu');
    
    hamburger.addEventListener('click', function() {
        hamburger.classList.toggle('active');
        navMenu.classList.toggle('active');
    });
    
    // Close menu when clicking on a link
    document.querySelectorAll('.nav-menu a').forEach(link => {
        link.addEventListener('click', function() {
            hamburger.classList.remove('active');
            navMenu.classList.remove('active');
        });
    });
});

// Smooth scrolling for navigation links
document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', function (e) {
        e.preventDefault();
        const target = document.querySelector(this.getAttribute('href'));
        if (target) {
            target.scrollIntoView({
                behavior: 'smooth',
                block: 'start'
            });
        }
    });
});

// Navbar background change on scroll
window.addEventListener('scroll', function() {
    const navbar = document.querySelector('.navbar');
    if (window.scrollY > 50) {
        navbar.style.background = 'rgba(255, 255, 255, 0.98)';
    } else {
        navbar.style.background = 'rgba(255, 255, 255, 0.95)';
    }
});

// Intersection Observer for animations
const observerOptions = {
    threshold: 0.1,
    rootMargin: '0px 0px -50px 0px'
};

const observer = new IntersectionObserver(function(entries) {
    entries.forEach(entry => {
        if (entry.isIntersecting) {
            entry.target.style.animationDelay = '0.1s';
            entry.target.style.animationFillMode = 'both';
        }
    });
}, observerOptions);

// Observe elements for animation
document.querySelectorAll('.feature-card, .about-text, .about-image').forEach(el => {
    observer.observe(el);
});

// Add loading animation to buttons
document.querySelectorAll('.btn').forEach(button => {
    button.addEventListener('mouseover', function() {
        this.style.transform = 'translateY(-2px)';
    });
    
    button.addEventListener('mouseout', function() {
        this.style.transform = 'translateY(0)';
    });
});

// Add scroll-to-top functionality
window.addEventListener('scroll', function() {
    const scrollTop = window.pageYOffset || document.documentElement.scrollTop;
    
    if (scrollTop > 300) {
        if (!document.querySelector('.scroll-to-top')) {
            const scrollButton = document.createElement('button');
            scrollButton.className = 'scroll-to-top';
            scrollButton.innerHTML = '<i class="fas fa-chevron-up"></i>';
            scrollButton.style.cssText = `
                position: fixed;
                bottom: 30px;
                right: 30px;
                width: 50px;
                height: 50px;
                background: #2563eb;
                color: white;
                border: none;
                border-radius: 50%;
                cursor: pointer;
                font-size: 18px;
                box-shadow: 0 4px 15px rgba(37, 99, 235, 0.3);
                transition: all 0.3s ease;
                z-index: 1000;
            `;
            
            scrollButton.addEventListener('click', function() {
                window.scrollTo({
                    top: 0,
                    behavior: 'smooth'
                });
            });
            
            scrollButton.addEventListener('mouseover', function() {
                this.style.transform = 'scale(1.1)';
                this.style.boxShadow = '0 6px 20px rgba(37, 99, 235, 0.4)';
            });
            
            scrollButton.addEventListener('mouseout', function() {
                this.style.transform = 'scale(1)';
                this.style.boxShadow = '0 4px 15px rgba(37, 99, 235, 0.3)';
            });
            
            document.body.appendChild(scrollButton);
        }
    } else {
        const scrollButton = document.querySelector('.scroll-to-top');
        if (scrollButton) {
            scrollButton.remove();
        }
    }
});

// Statistics counter animation
function animateCounter(element, target, duration = 2000) {
    const start = 0;
    const increment = target / (duration / 16);
    let current = start;
    
    const timer = setInterval(function() {
        current += increment;
        if (current >= target) {
            element.textContent = target + (element.textContent.includes('+') ? '+' : element.textContent.includes('%') ? '%' : '');
            clearInterval(timer);
        } else {
            element.textContent = Math.floor(current) + (element.textContent.includes('+') ? '+' : element.textContent.includes('%') ? '%' : '');
        }
    }, 16);
}

// Animate statistics when they come into view
const statsObserver = new IntersectionObserver(function(entries) {
    entries.forEach(entry => {
        if (entry.isIntersecting) {
            const statElements = entry.target.querySelectorAll('.stat h3');
            statElements.forEach(stat => {
                const text = stat.textContent;
                const number = parseInt(text.replace(/[^\d]/g, ''));
                if (number > 0) {
                    animateCounter(stat, number);
                }
            });
            statsObserver.unobserve(entry.target);
        }
    });
}, { threshold: 0.5 });

const statsSection = document.querySelector('.stats');
if (statsSection) {
    statsObserver.observe(statsSection);
}

// MRT Timetable Functionality
class MRTTimetable {
    constructor() {
        this.timetableData = {};
        this.currentStation = '';
        this.clockElement = document.getElementById('clock');
        this.dayDisplay = document.getElementById('day-display');
        this.scheduleDiv = document.getElementById('schedule');
        this.platform1 = document.getElementById('platform1');
        this.platform2 = document.getElementById('platform2');
        this.arrivalMessage = document.getElementById('arrival-message');
        
        // Custom dropdown elements
        this.customDropdown = document.getElementById('station-dropdown');
        this.selectedOption = document.getElementById('selected-station');
        this.stationOptions = document.getElementById('station-options');
        this.stationColumns = document.querySelector('.station-columns');
        
        this.init();
    }
    
    async init() {
        await this.loadTimetableData();
        this.setupEventListeners();
        this.updateClock();
        this.setupStations();
        this.startClockInterval();
    }
    
    async loadTimetableData() {
        try {
            const response = await fetch('mrt-6.json');
            this.timetableData = await response.json();
            console.log('Timetable data loaded successfully');
        } catch (error) {
            console.error('Error loading timetable data:', error);
        }
    }
    
    setupEventListeners() {
        // Confirm button
        const confirmBtn = document.getElementById('confirm');
        confirmBtn.addEventListener('click', () => {
            this.showSchedule();
        });
        
        // First and Last train buttons
        document.getElementById('firstTrain').addEventListener('click', () => {
            this.showFirstTrain();
        });
        
        document.getElementById('lastTrain').addEventListener('click', () => {
            this.showLastTrain();
        });
        
        // Custom dropdown functionality
        this.selectedOption.addEventListener('click', () => {
            this.toggleDropdown();
        });
        
        this.selectedOption.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' || e.key === ' ') {
                e.preventDefault();
                this.toggleDropdown();
            }
        });
        
        // Close dropdown when clicking outside
        document.addEventListener('click', (e) => {
            if (!this.customDropdown.contains(e.target)) {
                this.closeDropdown();
            }
        });
    }
    
    setupStations() {
        const stations = [
            'Uttara North', 'Uttara Center', 'Uttara South', 'Pallabi', 'Mirpur-11',
            'Mirpur-10', 'Kazipara', 'Shewrapara', 'Agargoan', 'Bijoy Sarani',
            'Farmgate', 'Karwan Bazar', 'Shahbag', 'Dhaka University', 'Bangladesh Secretariat',
            'Motijheel', 'Kamalapur'
        ];
        
        // Clear existing options
        this.stationColumns.innerHTML = '';
        
        stations.forEach(station => {
            const option = document.createElement('div');
            option.className = 'station-option';
            option.textContent = station;
            option.addEventListener('click', () => {
                this.selectStation(station);
            });
            this.stationColumns.appendChild(option);
        });
    }
    
    selectStation(station) {
        this.currentStation = station;
        this.selectedOption.querySelector('span').textContent = station;
        this.closeDropdown();
        
        // Update selected state
        document.querySelectorAll('.station-option').forEach(option => {
            option.classList.remove('selected');
        });
        document.querySelector(`.station-option:contains("${station}")`);
        
        // Find and highlight the selected option
        document.querySelectorAll('.station-option').forEach(option => {
            if (option.textContent === station) {
                option.classList.add('selected');
            }
        });
    }
    
    toggleDropdown() {
        const isOpen = this.customDropdown.getAttribute('aria-expanded') === 'true';
        if (isOpen) {
            this.closeDropdown();
        } else {
            this.openDropdown();
        }
    }
    
    openDropdown() {
        this.customDropdown.setAttribute('aria-expanded', 'true');
        this.stationOptions.style.display = 'block';
    }
    
    closeDropdown() {
        this.customDropdown.setAttribute('aria-expanded', 'false');
        this.stationOptions.style.display = 'none';
    }
    
    updateClock() {
        const now = new Date();
        const options = { 
            timeZone: 'Asia/Dhaka', 
            hour: '2-digit', 
            minute: '2-digit', 
            second: '2-digit', 
            hour12: false 
        };
        
        if (this.clockElement) {
            this.clockElement.textContent = now.toLocaleTimeString('en-US', options);
        }
        
        this.updateDayDisplay(now);
    }
    
    updateDayDisplay(date) {
        if (!this.dayDisplay) return;
        
        const daysOfWeek = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'];
        const dayOfWeek = date.getDay();
        this.dayDisplay.textContent = daysOfWeek[dayOfWeek];
        
        // Add holiday styling for Fridays (weekly holiday in Bangladesh)
        if (dayOfWeek === 5) {
            this.dayDisplay.classList.add('holiday');
        } else {
            this.dayDisplay.classList.remove('holiday');
        }
    }
    
    startClockInterval() {
        setInterval(() => {
            this.updateClock();
        }, 1000);
    }
    
    showSchedule() {
        if (!this.currentStation) {
            alert('Please select a station first');
            return;
        }
        
        const stationData = this.timetableData[this.currentStation];
        if (!stationData) {
            alert('No timetable data available for this station');
            return;
        }
        
        this.displayPlatformInfo(stationData);
        this.scrollToSchedule();
    }
    
    displayPlatformInfo(stationData) {
        const now = new Date();
        const currentTime = now.toLocaleTimeString('en-US', { 
            timeZone: 'Asia/Dhaka', 
            hour: '2-digit', 
            minute: '2-digit', 
            hour12: false 
        });
        
        // Clear previous content
        this.platform1.innerHTML = '';
        this.platform2.innerHTML = '';
        
        let platformCount = 0;
        
        Object.keys(stationData).forEach(direction => {
            const times = stationData[direction];
            const platformElement = platformCount === 0 ? this.platform1 : this.platform2;
            
            // Create platform header
            const header = document.createElement('h3');
            header.textContent = `To ${direction}`;
            platformElement.appendChild(header);
            
            // Create time list
            const timeList = document.createElement('ul');
            timeList.className = 'time-list';
            
            // Get next few trains
            const nextTrains = this.getNextTrains(times, currentTime, 5);
            
            nextTrains.forEach((time, index) => {
                const listItem = document.createElement('li');
                
                const timeSpan = document.createElement('span');
                timeSpan.className = 'time';
                timeSpan.textContent = time;
                
                const statusSpan = document.createElement('span');
                statusSpan.className = 'status';
                
                if (index === 0) {
                    statusSpan.textContent = 'Next Train';
                    statusSpan.className = 'status next-train';
                } else {
                    const timeDiff = this.getTimeDifference(currentTime, time);
                    statusSpan.textContent = `in ${timeDiff} min`;
                }
                
                listItem.appendChild(timeSpan);
                listItem.appendChild(statusSpan);
                timeList.appendChild(listItem);
            });
            
            platformElement.appendChild(timeList);
            platformCount++;
        });
    }
    
    getNextTrains(times, currentTime, count) {
        const current = this.timeToMinutes(currentTime);
        const nextTrains = [];
        
        for (let time of times) {
            const trainTime = this.timeToMinutes(time);
            if (trainTime >= current) {
                nextTrains.push(time);
                if (nextTrains.length >= count) break;
            }
        }
        
        // If we don't have enough trains for today, add some from tomorrow
        if (nextTrains.length < count) {
            const remaining = count - nextTrains.length;
            for (let i = 0; i < remaining && i < times.length; i++) {
                nextTrains.push(times[i] + ' (next day)');
            }
        }
        
        return nextTrains;
    }
    
    timeToMinutes(timeString) {
        const [hours, minutes] = timeString.split(':').map(Number);
        return hours * 60 + minutes;
    }
    
    getTimeDifference(currentTime, trainTime) {
        const current = this.timeToMinutes(currentTime);
        const train = this.timeToMinutes(trainTime);
        return Math.max(0, train - current);
    }
    
    scrollToSchedule() {
        const scheduleSection = document.querySelector('.platform-info-container');
        if (scheduleSection) {
            scheduleSection.scrollIntoView({ behavior: 'smooth' });
        }
    }
    
    showFirstTrain() {
        if (!this.currentStation) {
            alert('Please select a station first');
            return;
        }
        
        const stationData = this.timetableData[this.currentStation];
        if (!stationData) {
            alert('No timetable data available for this station');
            return;
        }
        
        let message = `<h3>First Trains from ${this.currentStation}:</h3>`;
        Object.keys(stationData).forEach(direction => {
            const firstTrain = stationData[direction][0];
            message += `<p><strong>To ${direction}:</strong> ${firstTrain}</p>`;
        });
        
        this.showArrivalMessage(message);
    }
    
    showLastTrain() {
        if (!this.currentStation) {
            alert('Please select a station first');
            return;
        }
        
        const stationData = this.timetableData[this.currentStation];
        if (!stationData) {
            alert('No timetable data available for this station');
            return;
        }
        
        let message = `<h3>Last Trains from ${this.currentStation}:</h3>`;
        Object.keys(stationData).forEach(direction => {
            const times = stationData[direction];
            const lastTrain = times[times.length - 1];
            message += `<p><strong>To ${direction}:</strong> ${lastTrain}</p>`;
        });
        
        this.showArrivalMessage(message);
    }
    
    showArrivalMessage(message) {
        this.arrivalMessage.innerHTML = message;
        this.arrivalMessage.style.display = 'block';
        this.arrivalMessage.classList.add('show');
        
        // Auto-hide after 5 seconds
        setTimeout(() => {
            this.arrivalMessage.classList.remove('show');
            setTimeout(() => {
                this.arrivalMessage.style.display = 'none';
            }, 300);
        }, 5000);
    }
}

// Initialize MRT Timetable when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    // Only initialize if we're on a page that has the timetable elements
    if (document.getElementById('clock')) {
        new MRTTimetable();
    }
});
