import { useEffect, useRef } from 'react';
import toast from 'react-hot-toast';
import axios from 'axios';

const API_BASE = 'http://localhost:8000';

interface RealtimeStatus {
  total_anomalies: number;
  blocked_ips_count: number;
  ip_profiles: Record<string, {
    anomaly_count: number;
    avg_risk: number;
    blocked: boolean;
  }>;
}

export const useAnomalyNotifications = (enabled: boolean = true) => {
  const notifiedAnomalies = useRef<Set<string>>(new Set());
  const lastBlockedIPsCount = useRef<number>(0);
  const lastTotalAnomalies = useRef<number>(0);

  useEffect(() => {
    if (!enabled) return;

    const checkForAnomalies = async () => {
      try {
        const response = await axios.get<RealtimeStatus>(`${API_BASE}/api/security/realtime/status`);
        const data = response.data;

        // Check for new IP blocks
        if (data.blocked_ips_count > lastBlockedIPsCount.current) {
          const newBlocks = data.blocked_ips_count - lastBlockedIPsCount.current;
          toast.error(
            `🚫 ${newBlocks} new IP${newBlocks > 1 ? 's' : ''} blocked for security violations!`,
            {
              duration: 6000,
              style: {
                background: '#ef4444',
                color: '#fff',
                border: '2px solid #dc2626',
                fontWeight: 'bold',
              },
            }
          );
          lastBlockedIPsCount.current = data.blocked_ips_count;
        }

        // Check for critical anomalies (IPs with 4+ anomalies not yet blocked - at risk)
        Object.entries(data.ip_profiles).forEach(([ip, profile]) => {
          const notificationId = `${ip}-${profile.anomaly_count}`;
          
          // Critical: 4+ anomalies (about to be blocked)
          if (profile.anomaly_count >= 4 && !profile.blocked && !notifiedAnomalies.current.has(notificationId)) {
            toast.error(
              `⚠️ Critical: IP ${ip} has ${profile.anomaly_count} anomalies (${(profile.avg_risk * 100).toFixed(0)}% avg risk)`,
              {
                duration: 8000,
                icon: '🔴',
                style: {
                  background: '#dc2626',
                  color: '#fff',
                  border: '2px solid #b91c1c',
                },
              }
            );
            notifiedAnomalies.current.add(notificationId);
          }
          
          // High: 2-3 anomalies
          else if (profile.anomaly_count >= 2 && profile.anomaly_count < 4 && !profile.blocked && !notifiedAnomalies.current.has(notificationId)) {
            toast(
              `⚠️ Warning: IP ${ip} has ${profile.anomaly_count} anomalies (${(profile.avg_risk * 100).toFixed(0)}% avg risk)`,
              {
                duration: 5000,
                icon: '🟠',
                style: {
                  background: '#f59e0b',
                  color: '#fff',
                  border: '2px solid #d97706',
                },
              }
            );
            notifiedAnomalies.current.add(notificationId);
          }
        });

        // Check for surge in anomalies
        if (data.total_anomalies > lastTotalAnomalies.current + 10) {
          const surgeDelta = data.total_anomalies - lastTotalAnomalies.current;
          toast.error(
            `🚨 Anomaly Surge Detected: +${surgeDelta} new anomalies in the last 5 seconds!`,
            {
              duration: 7000,
              style: {
                background: '#dc2626',
                color: '#fff',
                border: '2px solid #b91c1c',
                fontWeight: 'bold',
              },
            }
          );
        }
        lastTotalAnomalies.current = data.total_anomalies;

        // Cleanup old notifications (keep last 100)
        if (notifiedAnomalies.current.size > 100) {
          const items = Array.from(notifiedAnomalies.current);
          notifiedAnomalies.current = new Set(items.slice(-100));
        }

      } catch (error) {
        // Silently fail to avoid spamming console during backend downtime
        console.debug('Anomaly check failed:', error);
      }
    };

    // Initial check
    checkForAnomalies();

    // Poll every 5 seconds
    const interval = setInterval(checkForAnomalies, 5000);

    return () => clearInterval(interval);
  }, [enabled]);

  return {
    clearNotifications: () => {
      notifiedAnomalies.current.clear();
      lastBlockedIPsCount.current = 0;
      lastTotalAnomalies.current = 0;
    },
  };
};

export default useAnomalyNotifications;
