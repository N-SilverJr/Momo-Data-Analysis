/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./index.html",
    "./src/**/*.{html,js,jsx}"
  ],
  theme: {
    extend: {
      animation: {
        'slide-in': 'slideIn 0.3s ease-out'
      },
      keyframes: {
        slideIn: {
          'from': { transform: 'translateY(-50px)', opacity: '0' },
          'to': { transform: 'translateY(0)', opacity: '1' }
        }
      }
    }
  },
  plugins: []
}
