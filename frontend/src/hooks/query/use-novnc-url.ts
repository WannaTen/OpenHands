import { useQuery } from "@tanstack/react-query";
import { useTranslation } from "react-i18next";
import { useSelector } from "react-redux";
import OpenHands from "#/api/open-hands";
import { useConversation } from "#/context/conversation-context";
import { I18nKey } from "#/i18n/declaration";
import { RootState } from "#/store";
import { RUNTIME_INACTIVE_STATES } from "#/types/agent-state";
import { transformNovncUrl } from "#/utils/novnc-url-helper";

// Define the return type for the NoVNC URL query
interface NovncUrlResult {
  url: string | null;
  error: string | null;
}

export const useNovncUrl = () => {
  const { t } = useTranslation();
  const { conversationId } = useConversation();
  const { curAgentState } = useSelector((state: RootState) => state.agent);
  const isRuntimeInactive = RUNTIME_INACTIVE_STATES.includes(curAgentState);

  return useQuery<NovncUrlResult>({
    queryKey: ["novnc_url", conversationId],
    queryFn: async () => {
      if (!conversationId) throw new Error("No conversation ID");
      const data = await OpenHands.getNovncUrl(conversationId);
      if (data.novnc_url) {
        return {
          url: transformNovncUrl(data.novnc_url),
          error: null,
        };
      }
      return {
        url: null,
        error: t(I18nKey.NOVNC$URL_NOT_AVAILABLE),
      };
    },
    enabled: !!conversationId && !isRuntimeInactive,
    refetchOnMount: true,
    retry: 3,
  });
};
