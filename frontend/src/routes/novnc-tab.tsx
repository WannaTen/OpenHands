import React from "react";
import { useTranslation } from "react-i18next";
import { useSelector } from "react-redux";
import { I18nKey } from "#/i18n/declaration";
import { RootState } from "#/store";
import { RUNTIME_INACTIVE_STATES } from "#/types/agent-state";
import { useNovncUrl } from "#/hooks/query/use-novnc-url";

function NovncTab() {
  const { t } = useTranslation();
  const { data, isLoading, error } = useNovncUrl();
  const { curAgentState } = useSelector((state: RootState) => state.agent);
  const isRuntimeInactive = RUNTIME_INACTIVE_STATES.includes(curAgentState);
  const iframeRef = React.useRef<HTMLIFrameElement>(null);

  if (isRuntimeInactive) {
    return (
      <div className="w-full h-full flex items-center text-center justify-center text-2xl text-tertiary-light">
        {t("DIFF_VIEWER$WAITING_FOR_RUNTIME")}
      </div>
    );
  }

  if (isLoading) {
    return (
      <div className="w-full h-full flex items-center text-center justify-center text-2xl text-tertiary-light">
        {t("DIFF_VIEWER$WAITING_FOR_RUNTIME")}
      </div>
    );
  }

  if (error || (data && data.error) || !data?.url) {
    return (
      <div className="w-full h-full flex items-center text-center justify-center text-2xl text-tertiary-light">
        {data?.error || String(error) || t(I18nKey.NOVNC$URL_NOT_AVAILABLE)}
      </div>
    );
  }

  return (
    <div className="h-full w-full">
      <iframe
        ref={iframeRef}
        title={t(I18nKey.NOVNC$TITLE)}
        src={data.url}
        className="w-full h-full border-0"
        allow="clipboard-read; clipboard-write"
      />
    </div>
  );
}

// Export the NovncTab directly since we're using the provider at a higher level
export default NovncTab;
