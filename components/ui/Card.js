
import React from 'react';
import { 
  Card as FluentCard, 
  CardHeader, 
  CardPreview, 
  CardFooter 
} from '@fluentui/react-components';

const Card = ({ 
  children, 
  header,
  headerMedia,
  preview,
  footer,
  size = 'medium',
  appearance = 'outline',
  orientation = 'vertical',
  ...props 
}) => {
  return (
    <FluentCard
      size={size}
      appearance={appearance}
      orientation={orientation}
      {...props}
    >
      {(header || headerMedia) && (
        <CardHeader
          header={header}
          media={headerMedia}
        />
      )}

      {preview && (
        <CardPreview>
          {preview}
        </CardPreview>
      )}

      {children}

      {footer && (
        <CardFooter>
          {footer}
        </CardFooter>
      )}
    </FluentCard>
  );
};

export default Card;
