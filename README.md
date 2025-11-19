# Knife Tracker App

**Knife Tracker App** is a mobile application built with **Expo + React Native + Expo Router** designed to track CS2 knife listings in real time.

The app allows users to:

- View real-time knife listings  
- Filter by knife type  
- See price, float value, and image  
- Receive notifications when new knives appear  
- Sync with a FastAPI backend that performs scraping and background monitoring  

The project runs on both iOS and Android (with a Dev Client for notifications).

---

## 🚀 Tech Stack

### **Frontend**  
- Swift (SwiftUI)  
- APNs (Apple Push Notification Service)  
- URLSession para networking  
- Codable para parsing de JSON  
- UserDefaults / Keychain para armazenamento local  
- Gestão de filtros e categorias por dispositivo  
- Sincronização de push tokens com o backend  
- Async/await para operações assíncronas  
- UI responsiva e nativa em SwiftUI  

### **Backend**  
- FastAPI  
- MongoDB  
- Background worker (Python)  
- Expo Push Notifications API

---

  ## 📱 Platform Support

- **iOS** (Dev Client recommended)  
- **Android**  
- **Expo Go** (works but without notifications)  

---

## 📄 License — MIT

This project is licensed under the **MIT License**.  
You are free to use, modify, distribute, and reproduce the software as long as the original license notice is included.
