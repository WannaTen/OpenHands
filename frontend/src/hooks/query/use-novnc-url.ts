import { useQuery } from "@tanstack/react-query";
import { useTranslation } from "react-i18next";
import OpenHands from "#/api/open-hands";
import { useConversationId } from "#/hooks/use-conversation-id";
import { I18nKey } from "#/i18n/declaration";
import { transformNovncUrl } from "#/utils/novnc-url-helper";
import { useRuntimeIsReady } from "#/hooks/use-runtime-is-ready";

// Define the return type for the NoVNC URL query
interface NovncUrlResult {
  url: string | null;
  error: string | null;
}

export const useNovncUrl = () => {
  const { t } = useTranslation();
  const { conversationId } = useConversationId();
  const runtimeIsReady = useRuntimeIsReady();

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
    enabled: runtimeIsReady && !!conversationId,
    refetchOnMount: true,
    retry: 3,
  });
};
