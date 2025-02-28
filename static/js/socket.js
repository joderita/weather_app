document.addEventListener('DOMContentLoaded', function() {
    const socket = io();
    
    //Debug
    socket.on('connect', function() {
        console.log('Connected to WebSocket server');
    });
    
    socket.on('disconnect', function() {
        console.log('Disconnected from WebSocket server');
    });
    
    // Listen for flag changes
    socket.on('flag_change', function(data) {
        console.log('Flag change received:', data);
        if (data.key === 'wind_speeds') {
            if (window.location.pathname.includes('/weather')) {
                console.log('Reloading page due to wind_speeds flag change');
                
                const urlParams = new URLSearchParams(window.location.search);
                const city = urlParams.get('city') || 'Seattle';
                window.location.href = `/weather?city=${city}`;
            }
        }
    });
}); 